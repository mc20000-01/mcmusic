/** Shared helpers. Importing this module also boots auth and the API adapter,
 * so it must be imported once before any component mounts.
 */

import "./auth";
import "./net/api";

export const titleCase = (str: string) => str.split(" ")
    .map(w => w[0].toUpperCase() + w.slice(1))
    .join(" ");