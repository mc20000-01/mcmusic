import { useEffect, useRef } from "preact/hooks";
import type { Signal } from "@preact/signals";
import { Input } from "flufi-ui/components";

/**
 * flufi-ui's Input does not take a `type`, so the field is flipped to a
 * password input on mount (kept as an actual input, not CSS masking).
 */
export function PasswordInput(props: { value: Signal<string>, placeholder?: string }) {
    const ref = useRef<HTMLInputElement>(null);
    useEffect(() => {
        if (ref.current) ref.current.type = "password";
    }, []);
    return <Input value={props.value} inputRef={ref} placeholder={props.placeholder} />;
}
