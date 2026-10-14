from flask import Flask, render_template_string

app = Flask(__name__)

PAGE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#030615">
  <title>Website Under Maintenance</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    :root { color-scheme: dark; }
    * { box-sizing: border-box; }
    body {
      margin: 0; min-height: 100vh; overflow: hidden;
      background:
        radial-gradient(ellipse at 50% 44%, rgba(18, 49, 139, .30), transparent 42%),
        radial-gradient(ellipse at 50% 110%, rgba(93, 25, 190, .16), transparent 45%),
        #030615;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    .orb { position: fixed; width: 22rem; height: 22rem; border-radius: 50%;
      filter: blur(95px); opacity: .17; pointer-events: none; animation: drift 9s ease-in-out infinite alternate; }
    .orb.one { background: #00c8ff; top: -13rem; left: -8rem; }
    .orb.two { background: #a855f7; bottom: -15rem; right: -7rem; animation-delay: -4s; }
    .line { position: fixed; width: 28rem; height: 18rem; border: 1px solid rgba(38, 111, 255, .75);
      border-color: transparent transparent rgba(38, 111, 255, .8) rgba(38, 111, 255, .8);
      border-radius: 50%; transform: rotate(28deg); pointer-events: none;
      filter: drop-shadow(0 0 7px #236dff); }
    .line.top { top: -13rem; left: -10rem; }
    .line.bottom { bottom: -14rem; right: -10rem; transform: rotate(208deg); border-color: transparent transparent rgba(190, 45, 255, .8) rgba(190, 45, 255, .8); }
    .headline {
      color: #fff; letter-spacing: -.055em; line-height: .94;
      text-shadow: 0 0 18px rgba(0, 195, 255, .30), 0 0 48px rgba(134, 51, 255, .22);
    }
    .gradient-text {
      background: linear-gradient(100deg, #29e6ff 0%, #438aff 48%, #df59ff 100%);
      -webkit-background-clip: text; background-clip: text; color: transparent;
      filter: drop-shadow(0 0 20px rgba(58, 115, 255, .28));
    }
    .pulse-dot { box-shadow: 0 0 12px #27e7ff; animation: pulse 1.8s infinite; }
    .progress-fill { background: linear-gradient(90deg, #13e4ff, #6276ff, #dc4cff); box-shadow: 0 0 15px rgba(55, 177, 255, .75); }
    @keyframes pulse { 50% { opacity: .45; transform: scale(.85); } }
    @keyframes drift { to { transform: translate(35px, 25px) scale(1.12); } }
    @media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation: none !important; } }
  </style>
</head>
<body class="text-white">
  <div class="orb one"></div><div class="orb two"></div>
  <div class="line top"></div><div class="line bottom"></div>

  <main class="relative z-10 flex min-h-screen items-center justify-center px-5 py-12 text-center">
    <section class="w-full max-w-6xl">
      <div class="mx-auto mb-8 flex h-20 w-20 items-center justify-center rounded-2xl border border-cyan-300/20 bg-cyan-300/5 text-cyan-300 shadow-[0_0_45px_rgba(0,195,255,.16)]">
        <svg viewBox="0 0 64 64" fill="none" class="h-12 w-12" aria-hidden="true">
          <path d="M23 17 8 32l15 15M41 17l15 15-15 15M36 10 28 54" stroke="currentColor" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>

      <div class="mb-5 flex items-center justify-center gap-3 text-xs font-semibold uppercase tracking-[.35em] text-slate-300 sm:text-sm">
        <span class="pulse-dot h-2 w-2 rounded-full bg-cyan-300"></span>
        Website is currently
      </div>

      <h1 class="headline mx-auto text-[clamp(3rem,11vw,9rem)] font-black uppercase">
        <span class="gradient-text block">Under</span>
        <span class="block mt-2">Maintenance</span>
      </h1>

      <p class="mt-7 font-mono text-lg tracking-[.24em] text-cyan-200 sm:text-2xl">maintenance.py</p>
      <p class="mx-auto mt-6 max-w-xl text-sm leading-7 text-slate-400 sm:text-base">
        We’re making things better behind the scenes.<br>
        Please check back soon.
      </p>

      <div class="mx-auto mt-10 h-1.5 w-56 overflow-hidden rounded-full border border-blue-400/40 bg-slate-900 sm:w-80">
        <div class="progress-fill h-full w-2/3 rounded-full"></div>
      </div>
      <p class="mt-4 text-[10px] uppercase tracking-[.28em] text-slate-600">Temporarily offline · Back soon</p>
    </section>
  </main>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(PAGE)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
