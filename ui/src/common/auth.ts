import { signal, type Signal } from "@preact/signals";
import type { Option } from "flufi-ui/types";
import type { User } from "./net/types";
import { API, userFromJson } from "./net/api";

// mcmusic keeps the session in an HttpOnly cookie: the browser never holds a
// token, so "auth" here is just a flag that we know the server accepted us.
export type Auth = { type: "local"; token: "cookie" };

const auth: Signal<Option<Auth>> = signal(null);
const primaryServerAuth: Signal<Option<Auth>> = signal(null);

export const currentUser: Signal<Option<User>> = signal(null);
export const authCheckDone: Signal<boolean> = signal(false);

export const getAuth = () => auth.value;
export const peekAuth = () => auth.peek();
export const getAuthSignal = () => auth;
export const setAuth = (tkn: Auth) => {
    auth.value = tkn;
    primaryServerAuth.value = tkn;
};
export const peekPrimaryServerAuth = () => primaryServerAuth.peek();

export async function login(username: string, password: string): Promise<User> {
    const data = await API.login(username.trim(), password);
    const user = userFromJson(data);
    currentUser.value = user;
    setAuth({ type: "local", token: "cookie" });
    return user;
}

export async function register(data: {
    username: string; password: string; invite?: string; email?: string;
}): Promise<User> {
    const res = await API.register({ ...data, username: data.username.trim() });
    const user = userFromJson(res);
    currentUser.value = user;
    setAuth({ type: "local", token: "cookie" });
    return user;
}

export async function logout(): Promise<void> {
    try { await API.logout(); } catch { /* session is already gone */ }
    auth.value = null;
    primaryServerAuth.value = null;
    currentUser.value = null;
}

async function load() {
    try {
        const me = await API.me();
        currentUser.value = userFromJson(me);
        setAuth({ type: "local", token: "cookie" });
    } catch {
        auth.value = null;
    }
    authCheckDone.value = true;
}

load();
