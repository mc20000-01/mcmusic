import { useEffect, useRef, useState } from "preact/hooks";
import { useLocation } from "preact-iso";
import { Search, X } from "lucide-preact";

import "./style.css";
import type { SearchItem } from "../../common/net/types";
import { API } from "../../common/net/api";
import { SearchItemElem } from "./SearchItem";
import { Container, IconButton, Input, PopoutContainer } from "flufi-ui/components";
import type { Option } from "flufi-ui/types";
import { useSignal } from "@preact/signals";

/**
 * Topbar search with a debounced popout. flufi's Input handles the field and
 * PopoutContainer positions the result list; the only custom CSS left is the
 * popout width.
 */
export function SearchBar() {
    const inputRef = useRef<HTMLInputElement>(null);
    const loc = useLocation();
    const [query, setQuery] = useState("");
    const results = useSignal<Option<SearchItem[]>>(null);
    const open = useSignal<boolean>(false);

    function doFetch(value: string = query) {
        if (!value)
            return;
        API.search(value)
            .then((data) => {
                if (document.activeElement == inputRef.current) {
                    results.value = data;
                    open.value = data != null && data.length > 0;
                }
            })
            .catch(() => {
                results.value = null;
                open.value = false;
            });
    }

    function clear() {
        setQuery("");
        results.value = null;
        open.value = false;
        inputRef.current?.focus();
    }

    useEffect(() => {
        if (query) {
            const timer = setTimeout(() => doFetch(), 250);
            return () => clearTimeout(timer);
        } else {
            results.value = null;
            open.value = false;
        }
    }, [query]);

    useEffect(() => {
        results.subscribe((r) => {
            open.value = r != null && r.length > 0;
        })
    }, []);

    useEffect(() => {
        const input = inputRef.current;
        if (!input)
            return;
        // The global "/" shortcut focuses this field by id.
        input.id = "global-search";

        function onKeyDown(e: KeyboardEvent) {
            if (e.key == "Escape") {
                e.preventDefault();
                clear();
                input!.blur();
            }
        }

        input.addEventListener("keydown", onKeyDown);
        return () => input.removeEventListener("keydown", onKeyDown);
    }, []);

    return (
        <PopoutContainer
            open={open}
            popoutClass="search-popout"
            popout={() => (
                <Container vertical>
                    {results.value!.map(i => (
                        <SearchItemElem
                            item={i}
                            close={() => {
                                open.value = false;
                            }}
                        />
                    ))}
                </Container>
            )}
        >
            <Container horizontal centered_y class="search-bar">
                <Input
                    class="search-input"
                    inputRef={inputRef}
                    placeholder="Search"
                    value={query}
                    onInput={setQuery}
                    onEnter={(value: string) => {
                        const q = (value ?? query).trim();
                        if (q) {
                            open.value = false;
                            loc.route(`/search?q=${encodeURIComponent(q)}`);
                        }
                    }}
                />
                {query
                    ? (
                        <IconButton title="Clear search" onClick={clear}>
                            <X size={15} />
                        </IconButton>
                    )
                    : (
                        <IconButton title="Search" onClick={() => doFetch()}>
                            <Search size={15} />
                        </IconButton>
                    )}
            </Container>
        </PopoutContainer>
    )
}
