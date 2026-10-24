import { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import type { DataCenter, Hotspot, Pile } from "./api";

export default function MapView(props: {
  dataCenters: DataCenter[];
  selectedDC?: DataCenter;
  piles: Pile[];
  hotspots: Hotspot[];
}) {
  const ref = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const layer = useRef<maplibregl.Marker[]>([]);

  useEffect(() => {
    if (!ref.current || mapRef.current) return;
    mapRef.current = new maplibregl.Map({
      container: ref.current,
      style: "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
      center: [-71.2, 42.4],
      zoom: 9,
    });
  }, []);

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
  }, [props.dataCenters, props.piles, props.hotspots, props.selectedDC]);

  return <div ref={ref} className="map" />;
}
