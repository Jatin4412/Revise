import styles from "./page.module.css";

export default function Home() {
  return (
    <main className={styles.page}>
      <section className={styles.card} aria-labelledby="welcome-title">
        <span className={styles.eyebrow}>REITERATE</span>
        <h1 id="welcome-title">The UI foundation is ready.</h1>
        <p>
          This is the web boundary for the Reiterate engine. UI state, components,
          and engine communication will live here without coupling the interface to
          engine internals.
        </p>
      </section>
    </main>
  );
}
