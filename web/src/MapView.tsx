import { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import type { DataCenter, Hotspot, Pile } from "./api";

export default function MapView(props: {
  dataCenters: DataCenter[];
  selectedDC?: DataCenter;
  piles: Pile[];
  farms?: Pile[];
  hotspots: Hotspot[];
  terrain?: boolean;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const layer = useRef<maplibregl.Marker[]>([]);

  useEffect(() => {
    if (!ref.current || mapRef.current) return;
    const map = new maplibregl.Map({
      container: ref.current,
      style: "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
      center: [-71.2, 42.4],
      zoom: 9,
    });
    mapRef.current = map;
    // USGS 3DEP hillshade as a raster source (added once; toggled via opacity).
    map.on("load", () => {
      map.addSource("usgs-hillshade", {
        type: "raster",
        tiles: [
          "https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer/exportImage?bbox={bbox-epsg-3857}&bboxSR=3857&imageSR=3857&size=256,256&format=png&transparent=true&renderingRule=%7B%22rasterFunction%22%3A%22Hillshade%20Gray%22%7D&f=image",
        ],
        tileSize: 256,
        attribution: "USGS 3DEP",
      });
      map.addLayer({
        id: "usgs-hillshade",
        type: "raster",
        source: "usgs-hillshade",
        paint: { "raster-opacity": 0 },
      });
    });
  }, []);

  // Toggle terrain layer opacity.
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const apply = () => {
      if (map.getLayer("usgs-hillshade")) {
        map.setPaintProperty("usgs-hillshade", "raster-opacity", props.terrain ? 0.55 : 0);
      }
    };
    if (map.isStyleLoaded()) apply();
    else map.once("idle", apply);
  }, [props.terrain]);

  // Recenter on the selected data center.
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !props.selectedDC) return;
    map.flyTo({ center: [props.selectedDC.lon, props.selectedDC.lat], zoom: 10, speed: 0.8 });
  }, [props.selectedDC]);

  // Redraw all markers.
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    layer.current.forEach((m) => m.remove());
    layer.current = [];

    // Data centers (red squares).
    for (const dc of props.dataCenters) {
      const el = document.createElement("div");
      el.className = "dc-marker";
      if (props.selectedDC && dc.name === props.selectedDC.name) el.classList.add("selected");
      const m = new maplibregl.Marker({ element: el })
        .setLngLat([dc.lon, dc.lat])
        .setPopup(new maplibregl.Popup().setHTML(
          `<b>${dc.operator} — ${dc.name}</b><br/>${dc.city}<br/><small>${dc.note}</small>`
        ))
        .addTo(map);
      layer.current.push(m);
    }

    // City snow FARMS (white snowflake markers — collection points, distinct from piles).
    for (const f of props.farms ?? []) {
      const el = document.createElement("div");
      el.className = "farm-marker";
      el.textContent = "❄";
      const m = new maplibregl.Marker({ element: el })
        .setLngLat([f.lon, f.lat])
        .setPopup(new maplibregl.Popup().setText(`Snow farm: ${f.name}`))
        .addTo(map);
      layer.current.push(m);
    }

    // Snow piles (blue circles sized by mass).
    const maxT = Math.max(1, ...props.piles.map((p) => p.tonnes));
    for (const p of props.piles) {
      const el = document.createElement("div");
      el.className = "pile-marker";
      const size = 10 + 22 * (p.tonnes / maxT);
      el.style.width = `${size}px`;
      el.style.height = `${size}px`;
      const m = new maplibregl.Marker({ element: el })
        .setLngLat([p.lon, p.lat])
        .setPopup(new maplibregl.Popup().setText(`${p.name}: ${p.tonnes.toLocaleString()} t snow`))
        .addTo(map);
      layer.current.push(m);
    }

    // Hotspots (green->red by score).
    for (const h of props.hotspots) {
      const el = document.createElement("div");
      el.className = "hot-marker";
      const hue = 120 - 120 * h.score; // 120=green (low), 0=red... invert: high score = hot
      el.style.background = `hsla(${120 - hue}, 85%, 50%, 0.75)`;
      const m = new maplibregl.Marker({ element: el })
        .setLngLat([h.lon, h.lat])
        .setPopup(new maplibregl.Popup().setHTML(
          `<b>${h.name}</b><br/>Score: <b>${(h.score * 100).toFixed(0)}</b>/100<br/>` +
          `Elev ${h.elevation_m} m · slope ${h.slope_deg}° · ${h.distance_km} km to DC`
        ))
        .addTo(map);
      layer.current.push(m);
    }
  }, [props.dataCenters, props.piles, props.farms, props.hotspots, props.selectedDC]);

  return <div ref={ref} className="map" />;
}
