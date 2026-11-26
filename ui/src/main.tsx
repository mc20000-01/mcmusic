/** Entry point: load locally bundled fonts and flufi-ui's stylesheet, run the
 * auth/API bootstrap, then mount the router app.
 */
import { render } from 'preact';
import { App } from './app.tsx';

import "@fontsource-variable/inter/index.css";
import "@fontsource-variable/jetbrains-mono/index.css";
import "@fontsource-variable/lexend/index.css";
import "flufi-ui/style.css";

import "./common/index";

render(<App />, document.getElementById('app')!)
