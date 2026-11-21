/** Cross-page booleans that are not server state (currently whether the user is
 * allowed to use the client at all).
 */
import { signal, type Signal } from "@preact/signals";
import type { Option } from "flufi-ui/types";

export const allowed: Signal<Option<boolean>> = signal(null);
