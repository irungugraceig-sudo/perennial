import Logo from "./Logo";

type View = "city" | "datacenter" | "impact";

export default function Hero({ onPick }: { onPick: (v: View) => void }) {
  return (
    <div className="hero">
      <div className="hero-inner">
        <div className="hero-logo"><Logo size={72} /></div>
        <h1>Perennial</h1>
        <p className="lede">
          AI data centers drank <b>17 billion gallons</b> of fresh water last year to stay cool.
          Snowy cities throw away free winter cold. <b>Perennial connects the two.</b>
        </p>
        <p className="sub">
          We turn a city's discarded snow into clean cooling for GPU data centers — and prove
          the water, energy, and carbon it saves.
        </p>

        <div className="hero-paths">
          <button className="path city" onClick={() => onPick("city")}>
            <span className="path-icon">🏙️</span>
            <span className="path-title">I'm a City</span>
            <span className="path-desc">Where is my snow, and what is it worth?</span>
          </button>
          <button className="path dc" onClick={() => onPick("datacenter")}>
            <span className="path-icon">🖥️</span>
            <span className="path-title">I'm a Data Center</span>
            <span className="path-desc">How much can I save — now and as I grow?</span>
          </button>
          <button className="path impact" onClick={() => onPick("impact")}>
            <span className="path-icon">🌍</span>
            <span className="path-title">The Impact</span>
            <span className="path-desc">Why this matters as AI scales to 2030.</span>
          </button>
        </div>

        <div className="name-story">
          <p>
            <b>Why "Perennial"?</b> Perennial snow is the glaciologist's term for snow that
            survives the melt season, cold that lasts from one winter into the next. The perilla
            is a hardy perennial herb that comes back every year. Both carry the same promise our
            product makes: winter's cold, kept alive and put to work in summer.
          </p>
        </div>

        <p className="hero-foot">
          Proven since 2000 by a Swedish hospital · Boston already piled snow 75 ft high in 2015
        </p>
      </div>
    </div>
  );
}
