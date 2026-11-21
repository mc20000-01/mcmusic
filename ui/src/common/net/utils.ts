/** Small parsing helpers for API payloads.
 */
import { generateAuthHeader, peekAuth, peekPrimaryServerAuth } from "../auth";
import { allowed } from "../state";

export async function authedFetch(
    input: URL | RequestInfo,
    init?: RequestInit,
    usePrimary?: boolean
): Promise<Response> {
    if (!(usePrimary && peekPrimaryServerAuth()))
        if (!peekAuth())
            throw `tried to auth fetch when no auth`;
    
    return await fetch(input, {
        ...init,
        headers: {
            ...init?.headers,
            "x-flufimusic-auth": generateAuthHeader(usePrimary)
        }
    });
}

//           network response (json) -vvv       vvvv- e.g. 'Server.login()'
export function handleFlufimusicError(res: any, func: string, primary: boolean) {
    if (!res.ok) {
        switch (res.err_type) {
            case "not_allowed": {
                if (primary)
                    allowed.value = false;
                
                break;
            }
        }
        
        throw `${func} failed${res.err_type != null ? " (" + res.err_type + ")" : ""}${res.err != null ? ": " + res.err : ""}`;
    }
}
