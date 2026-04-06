/**
 * Populate #city-events-root with upcoming vehicle events + rotating car imagery.
 * Expects data-city-slug and data-city-name on the root element.
 */
(function () {
  function hazeltineIsVehicleEventRaw(e) {
    var name = (e.name || '').toLowerCase();
    var full = (name + ' ' + (e.description || '') + ' ' + (e.venue_name || '')).toLowerCase();
    if (/brewing|big head todd|prenatal|egg hunt|puzzle contest|5k fun run/i.test(full)) return false;
    if (/lfa \d+|\bboxing\b|\bwrestling\b/i.test(name) && !/monster jam/i.test(name)) return false;
    if (/motorcycle/.test(name) && !/show|swap|meet|expo|rally|viking/i.test(name)) return false;
    return /car show|auto show|monster jam|monster truck|boat show|rv show|motorcycle|cruise-in|cruise night|cars & coffee|cars and coffee|autocross|swap meet|gsta|gmcca|spring extravaganza|roadsters|on-water boat|mowog|viking motorcycle|truck show|jeep fest|off-road expo|collector car|exotic car meet|car meet|camper show|motorhome/i.test(name);
  }

  function formatDate(dateStr) {
    var date = new Date(dateStr + 'T12:00:00');
    var days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    var months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return days[date.getDay()] + ', ' + months[date.getMonth()] + ' ' + date.getDate();
  }

  function truncate(str, len) {
    if (!str) return '';
    return str.length > len ? str.substring(0, len) + '…' : str;
  }

  function normalizeCity(s) {
    return (s || '').toLowerCase().replace(/[^a-z0-9]+/g, ' ').trim();
  }

  function cityMatches(slug, cityName, evCity) {
    var evN = normalizeCity(evCity);
    if (!evN) return false;
    var slugN = normalizeCity(slug.replace(/-/g, ' '));
    var nameN = normalizeCity(cityName);
    if (evN.indexOf(slugN) >= 0 || slugN.indexOf(evN) >= 0) return true;
    if (nameN && (evN.indexOf(nameN) >= 0 || nameN.indexOf(evN) >= 0)) return true;
    // St. Paul / Saint Paul
    if (/^st\.?\s*paul/.test(slugN) && /saint paul|st\.?\s*paul/.test(evN)) return true;
    return false;
  }

  function run() {
    var roots = document.querySelectorAll('[data-city-events-root]');
    if (!roots.length) return;

    var v = '?v=' + new Date().toISOString().slice(0, 10);
    Promise.all([
      fetch('data/events-master.json' + v).then(function (r) {
        if (!r.ok) throw new Error('events');
        return r.json();
      }),
      fetch('data/default-car-event-images.json?v=1').then(function (r) {
        return r.ok ? r.json() : { urls: [] };
      }).catch(function () { return { urls: [] }; })
    ]).then(function (pair) {
      var raw = pair[0];
      var pool = (pair[1] && pair[1].urls) ? pair[1].urls : [];
      var events = Array.isArray(raw) ? raw : (raw && Array.isArray(raw.events) ? raw.events : []);

      var now = new Date();
      now.setHours(0, 0, 0, 0);
      var horizon = new Date(now);
      horizon.setDate(horizon.getDate() + 30);

      roots.forEach(function (root) {
        var slug = root.getAttribute('data-city-slug') || '';
        var cityName = root.getAttribute('data-city-name') || '';

        var upcoming = events.filter(function (ev) {
          if (!ev.date || !hazeltineIsVehicleEventRaw(ev)) return false;
          var evDate = new Date(ev.date + 'T12:00:00');
          return evDate >= now && evDate <= horizon;
        });

        upcoming.sort(function (a, b) {
          return new Date(a.date) - new Date(b.date);
        });

        var localFirst = upcoming.filter(function (ev) {
          return cityMatches(slug, cityName, ev.city || '');
        });
        var rest = upcoming.filter(function (ev) {
          return !cityMatches(slug, cityName, ev.city || '');
        });
        var merged = localFirst.concat(rest);
        var pick = merged.slice(0, 8);

        if (!pick.length) {
          root.innerHTML = '<p class="city-events-empty">No upcoming vehicle events in the calendar window. Browse the full list on <a href="events.html">Events</a>.</p>';
          return;
        }

        var html = '<div class="events-scroll-wrapper"><div class="events-grid city-events-grid">';
        pick.forEach(function (ev, idx) {
          var hasImg = ev.image && String(ev.image).length > 0;
          var imgUrl = hasImg ? ev.image : (pool.length ? pool[idx % pool.length] : '');
          var imgBlock = imgUrl
            ? '<div class="event-image"><img src="' + imgUrl.replace(/"/g, '%22') + '" alt="" loading="lazy"></div>'
            : '<div class="event-image"></div>';
          var href = ev.url ? ev.url : 'events.html';
          var name = truncate(ev.name || 'Event', 72);
          var venue = truncate(ev.venue_name || '', 48);
          html += '<a class="event-card" href="' + href.replace(/"/g, '%22') + '" target="_blank" rel="noopener">' +
            imgBlock +
            '<div class="event-info">' +
            '<div class="event-date">' + formatDate(ev.date) + '</div>' +
            '<div class="event-name">' + name.replace(/</g, '&lt;') + '</div>' +
            '<div class="event-venue">' + (venue ? venue.replace(/</g, '&lt;') + ' · ' : '') + (ev.city || '').replace(/</g, '&lt;') + '</div>' +
            '<div class="event-cta">Details →</div>' +
            '</div></a>';
        });
        html += '</div></div>';
        root.innerHTML = html;
      });
    }).catch(function () {
      roots.forEach(function (root) {
        root.innerHTML = '<p class="city-events-empty">Events could not be loaded. Try <a href="events.html">Events</a>.</p>';
      });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', run);
  } else {
    run();
  }
})();
