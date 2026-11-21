/** Entry point: load flufi-ui's stylesheet, run the auth/API bootstrap, then
 * mount the router app.
 */
import { render } from 'preact';
import { App } from './app.tsx';

import "flufi-ui/style.css";

import "./common/index";

render(<App />, document.getElementById('app')!)
