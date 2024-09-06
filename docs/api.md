---
hide:
  - navigation
  - toc
---
<style>
    .md-typeset h1,
    .md-content__button {
        display: none;
    }
    .md-main__inner {
        max-width: 100%; /* or 100%, if you want to stretch to full-width */
        margin-top: 0;
    }
    .md-content__inner {
        margin: 0;
        padding-top: 0;
    }
    .md-content__inner > p {
        margin: 0;
    }
    .md-content__inner::before {
        display: none;
    }
    .md-footer__inner {
        display: none;
    }
    .md-footer__inner:not([hidden]) {
        display: none;
    }
</style>
<rapi-doc 
    spec-url="/api/openapi.json"
    theme = "dark"
    show-header = "false"
    show-info = "false"
    allow-authentication = "true"
    allow-server-selection = "true"
    allow-api-list-style-selection = "true"
    theme = "dark"
    render-style = "focused"
    bg-color="#1e2129"
    primary-color="#a47bea"
    regular-font="Roboto"
    mono-font="Roboto Mono"
    show-method-in-nav-bar="as-colored-text">
    <img slot="logo" style="display: none"/>
</rapi-doc>
<script 
    type="module" 
    src="https://unpkg.com/rapidoc/dist/rapidoc-min.js"
></script>
