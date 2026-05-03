import { theme as G, fonts } from "../../constants/theme";

// Card
export function Card({children, style}){
    return(
        <div style={{
            background: G.card,
            border: `1px solid ${G.border}`,
            borderRadius: 12,
            padding: 20,
            ...style,
        }}>
            {children}
        </div>
    );
}

//Pill/badge
export function Pill({color, children}){
    return(
        <span style={{
            display: "inline-flex", alignItems: "center", gap: 5,
            padding: "3px 10px", borderRadius: 99,
            background: color + "22",
            color,
            fontSize: 11, fontWeight: 500,
            fontFamily: fonts.mono, letterSpacing: "0.04em"
        }}>
            {children}
        </span>
    );
}

// Button
export function Button({children, onClick, disabled, variant = "primary", style}){
    const variants = {
        primary: {
            background: disabled ? G.accentLo: G.accent,
            color: disabled ? G.textSub: "#fff",
            border: "none",
        },
        ghost: {
            background: "transparent",
            color: G.textSub,
            border: `1px solid ${G.border}`,
        },
    };

    return(
        <button
            onClick={onClick}
            disabled={disabled}
            style={{
                padding: "10px 20px", borderRadius: 8,
                fontFamily: fonts.display, fontWeight: 700, fontSize: 14,
                cursor: disabled ? "not-allowed": "pointer",
                display: "inline-flex", alignItems: "center", justifyContent: "center", gap: 8,
                transition: "opacity 0.15s",
                ...variants[variant],
                ...style,
            }}
        >
            {children}
        </button>
    );
}

// Input
export function Input({label, value, onChange, placeholder, type = "text", multiline, required}){
    const baseStyle={
        width: "100%",
        background: G.surface,
        border: `1px solid ${G.border}`,
        borderRadius: 8,
        padding: "10px 14px",
        color: G.text,
        fontFamily: fonts.body,
        fontSize: 14,
        outline: "none",
        transition: "border-color 0.15s",
        resize: multiline ? "vertical": undefined,
        minHeight: multiline ? 110: undefined,
    };

    return(
        <div>
            {label && (
                <label style={{
                    display: "block",
                    color: G.textSub,
                    fontSize: 11,
                    marginBottom: 6,
                    letterSpacing: "0.06em",
                    textTransform: "uppercase",
                }}>
                    {label}{required && <span style={{color: G.danger}}> *</span>}
                </label>
            )}
            {multiline ? (
                <textarea
                    value={value}
                    onChange={e=>onChange(e.target.value)}
                    placeholder={placeholder}
                    style={baseStyle}
                    onFocus={e=>(e.target.style.borderColor = G.accent)}
                    onBlur={e=>(e.target.style.borderColor = G.border)}
                />
            ) : (
                <input
                    type={type}
                    value={value}
                    onChange={e=>onChange(e.target.value)}
                    placeholder={placeholder}
                    style={baseStyle}
                    onFocus={e=>(e.target.style.borderColor = G.accent)}
                    onBlur={e=>(e.target.style.borderColor = G.border)}
                />
            )}
        </div>
    );
}

//Spinner
export function Spinner({size = 20}){
    return(
        <div style={{
            width: size, height: size,
            borderRadius: "50%",
            border: `2px solid ${G.border}`,
            borderTopColor: G.accent,
            animation: "spin 0.7s linear infinite",
            display: "inline-block",
            flexShrink: 0,
        }} />
    );
}

// SectionTitle
export function SectionTitle({children, level = 2}){
    const Tag = `h${level}`;
    return(
        <Tag style={{
            fontFamily: fonts.display,
            fontWeight: 700,
            fontSize: 14,
            marginBottom: 14,
            color: G.text,
        }}>
            {children}
        </Tag>
    );
}