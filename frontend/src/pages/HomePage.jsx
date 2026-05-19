import { theme as G, fonts } from "../constants/theme";
import { Button } from "../components/ui";
import HootLogo from "../assets/hoot_logo.svg?react";
import { translation } from "../constants/translations";

export default function HomePage({ setPage, lang }) {
    const t = translation[lang].home;

    return (
        <div style={{ minHeight: "100vh", background: G.bg }}>
            {/*Hero*/}
            <section style={{
                display: "flex", flexDirection: "column", alignItems: "center",
                justifyContent: "center", minHeight: "calc(100vh-56px)",
                padding: "60px 24px", textAlign: "center",
            }}>
                <HootLogo width={150} height={150} style={{ marginBottom: 24 }} />
                <h1 style={{
                    fontFamily: fonts.display, fontSize: 72, fontWeight: 800,
                    letterSpacing: "-0.04em", color: G.text, marginBottom: 16, lineHeight: 1,
                }}>
                    HOOT
                </h1>
                <p style={{
                    fontFamily: fonts.display, fontSize: 20, fontWeight: 700,
                    color: G.accent, marginBottom: 16, letterSpacing: "0.08em",
                    textTransform: "uppercase",
                }}>
                    {t.slogan}
                </p>
                <p style={{
                    color: G.textSub, fontSize: 16, maxWidth: 480,
                    lineHeight: 1.6, marginBottom: 40,
                }}>
                    {t.subtitle}
                </p>
                <div style={{ display: "flex", gap: 12 }}>
                    <Button onClick={() => setPage("analyze")}
                        style={{ padding: "12px 28px", fontSize: 15 }}>
                        {t.cta}
                    </Button>
                    <Button variant="ghost" onClick={() => setPage("dashboard")}
                        style={{ padding: "12px 28px", fontSize: 15 }}>
                        {t.ctaSecondary}
                    </Button>
                </div>
            </section>

            {/*Features*/}
            <section style={{ padding: "80px 24px", maxWidth: 900, margin: "0 auto" }}>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 24 }}>
                    {[
                        { icon: "Aa", color: G.accent, title: t.feat1Title, desc: t.feat1Desc },
                        { icon: "◉", color: G.ok, title: t.feat2Title, desc: t.feat2Desc },
                        { icon: "✦", color: G.warn, title: t.feat3Title, desc: t.feat3Desc },
                    ].map(({ icon, color, title, desc }) => (
                        <div key={title} style={{
                            background: G.surface, border: `1px solid ${G.border}`,
                            borderRadius: 16, padding: "28px 24px",
                        }}>
                            <div style={{
                                width: 44, height: 44, borderRadius: 10,
                                background: color + "22", border: `1px solid ${color}44`,
                                display: "flex", alignItems: "center", justifyContent: "center",
                                fontFamily: fonts.mono, fontSize: 16, color, marginBottom: 16,
                            }}>
                                {icon}
                            </div>
                            <div style={{
                                fontFamily: fonts.display, fontWeight: 700,
                                fontSize: 15, color: G.text, marginBottom: 8,
                            }}>
                                {title}
                            </div>
                            <div style={{ color: G.textSub, fontSize: 13, lineHeight: 1.6 }}>
                                {desc}
                            </div>
                        </div>
                    ))}
                </div>
            </section>

            {/*Cómo funciona*/}
            <section style={{ padding: "0 24px 80px", maxWidth: 900, margin: "0 auto" }}>
                <h2 style={{
                    fontFamily: fonts.display, fontWeight: 800, fontSize: 28,
                    letterSpacing: "-0.03em", color: G.text, marginBottom: 40, textAlign: "center",
                }}>
                    {t.howTitle}
                </h2>
                <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 24 }}>
                    {[
                        { n: "01", title: t.step1Title, desc: t.step1Desc },
                        { n: "02", title: t.step2Title, desc: t.step2Desc },
                        { n: "03", title: t.step3Title, desc: t.step3Desc },
                    ].map(({ n, title, desc }) => (
                        <div key={n} style={{ textAlign: "center", padding: "0 16px" }}>
                            <div style={{
                                fontFamily: fonts.mono, fontSize: 40, fontWeight: 700,
                                color: G.accent + "55", marginBottom: 12, lineHeight: 1,
                            }}>
                                {n}
                            </div>
                            <div style={{
                                fontFamily: fonts.display, fontWeight: 700,
                                color: G.text, marginBottom: 12, fontSize: 15,
                            }}>
                                {desc}
                            </div>
                        </div>
                    ))}
                </div>
            </section>

            {/*Stats*/}
            <section style={{ borderTop: `1px solid ${G.border}`, padding: "40px 24px" }}>
                <div style={{
                    maxWidth: 900, margin: "0 auto",
                    display: "flex", justifyContent: "center", gap: 56, flexWrap: "wrap",
                }}>
                    {[
                        { label: t.stat2, value: "ES / EN" },
                        { label: t.stat3, value: "Llama 3.2" },
                    ].map(({ label, value }) => (
                        <div key={label} style={{ textAlign: "center" }}>
                            <div style={{
                                fontFamily: fonts.mono, fontSize: 24, fontWeight: 700,
                                color: G.accent, marginBottom: 4,
                            }}>
                                {value}
                            </div>
                            <div style={{ color: G.textSub, fontSize: 12 }}>
                                {label}
                            </div>
                        </div>
                    ))}
                </div>
            </section>
        </div>
    );
}