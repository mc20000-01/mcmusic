/** One empty state for lists and panels, so every page says "nothing here"
 * with the same icon, spacing and call to action.
 */
import type { ComponentChildren } from "preact";
import { TextIconButton } from "flufi-ui/components";
import { Inbox, RefreshCw } from "lucide-preact";

import "./style.css";

export function EmptyState(props: {
    icon?: ComponentChildren;
    title: string;
    body?: string;
    actionLabel?: string;
    onAction?: () => void;
    class?: string;
}) {
    return (
        <div class={`empty-state${props.class ? ` ${props.class}` : ""}`}>
            <span class="empty-state-icon" aria-hidden="true">
                {props.icon ?? <Inbox size={22} />}
            </span>
            <strong class="empty-state-title">{props.title}</strong>
            {props.body && <p class="empty-state-body">{props.body}</p>}
            {props.actionLabel && props.onAction && (
                <TextIconButton variant="panel" onClick={props.onAction}>
                    <RefreshCw size={15} /> {props.actionLabel}
                </TextIconButton>
            )}
        </div>
    );
}
