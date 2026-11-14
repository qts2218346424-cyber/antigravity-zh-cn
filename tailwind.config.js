import daisyui from "daisyui";
import containerQueries from "@tailwindcss/container-queries";

const baseColor = (variable) => `color-mix(in srgb, var(${variable}) calc(100% * <alpha-value>), transparent)`;

/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    darkMode: 'class',
    theme: {
        extend: {
            colors: {
                'base-100': baseColor('--color-base-100'),
                'base-200': baseColor('--color-base-200'),
                'base-300': baseColor('--color-base-300'),
                'base-content': baseColor('--color-base-content'),
            },
        },
    },
    plugins: [daisyui, containerQueries],
    daisyui: {
        themes: [
            {
                light: {
                    "primary": "#3b82f6",
                    "secondary": "#64748b",
                    "accent": "#10b981",
                    "neutral": "#1f2937",
                    "base-100": "#ffffff",
                    "info": "#0ea5e9",
                    "success": "#10b981",
                    "warning": "#f59e0b",
                    "error": "#ef4444",
                },
            },
            {
                dark: {
                    "primary": "#3b82f6",
                    "secondary": "#a1a1aa",
                    "accent": "#10b981",
                    "neutral": "#18181b",
                    "base-100": "#0b0c0e", // Deep obsidian dark base
                    "base-200": "#15161b", // Elevated rich slate-charcoal surface
                    "base-300": "#26272f", // Crisp borders and inputs
                    "base-content": "#f4f4f5",
                    "info": "#0ea5e9",
                    "success": "#10b981",
                    "warning": "#f59e0b",
                    "error": "#ef4444",
                },
            },
        ],
        darkTheme: "dark",
    },
}
