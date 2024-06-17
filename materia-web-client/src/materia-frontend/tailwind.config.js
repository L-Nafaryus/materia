/** @type {import('tailwindcss').Config} */
export default {
    content: ["./index.html", "./src/**/*.{vue,ts,js}"],
    theme: {
        extend: {
            keyframes: {
                "border-spin": {
                    "100%": {
                        transform: "rotate(-360deg)",
                    }
                },
                "border-roll": {
                    "100%": {
                        "background-position": "200% 0",
                    }
                }
            },
            animation: {
                "border-spin": "border-spin 7s linear infinite",
                "border-roll": "border-roll 5s linear infinite"
            }
        },
    },
    plugins: [],
}


