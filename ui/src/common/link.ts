/** URL builders for the UUID-based routes the v3 pages use.
 */
import type { Artist, Set, Uuid } from "./net/types";

export function artistLink(data: { uuid: Uuid, serverUrl: string } | { artist: Artist }): string {
    const uuid = "uuid" in data ? data.uuid : data.artist.uuid;
    
    // TODO: handle server url

    return `/artist/${uuid}`;
}

export function setLink(data: { uuid: Uuid, serverUrl: string } | { set: Set }): string {
    const uuid = "uuid" in data ? data.uuid : data.set.uuid;
    
    // TODO: handle server url
    
    return `/set/${uuid}`;
}
