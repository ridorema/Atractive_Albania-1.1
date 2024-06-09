var map = L.map('map').setView([41.3275, 19.8189], 7);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

function showMap(siteType) {
    fetch(`/sites/${siteType}`)
        .then(response => response.json())
        .then(data => {
            map.eachLayer(function (layer) {
                if (!!layer.toGeoJSON) {
                    map.removeLayer(layer);
                }
            });

            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            }).addTo(map);

            data.forEach(site => {
                L.marker([site.lat, site.lng]).addTo(map)
                    .bindPopup(`<b>${site.name}</b><br><a href="/site/${site.id}">More info</a>`);
            });
        });
}
