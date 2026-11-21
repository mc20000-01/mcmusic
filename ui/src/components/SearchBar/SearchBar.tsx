import { useEffect, useRef, useState } from "preact/hooks";
import { Search } from "lucide-preact";

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
    const [query, setQuery] = useState("");
    const results = useSignal<Option<SearchItem[]>>(null);
    const open = useSignal<boolean>(false);

    function doFetch() {
        if (query)
            API.search(query)
                .then((data) => {
                    if (document.activeElement == inputRef.current) {
                        results.value = data;
                    }
                })
                .catch(() => {});
    }

    function resetResults() {
        results.value = null;
    }

    useEffect(() => {
        if (query) {
            const timer = setTimeout(doFetch, 250);
            return () => clearTimeout(timer);
        } else {
            resetResults();
        }
    }, [query]);

    useEffect(() => {
        results.subscribe((r) => {
            open.value = r != null && r.length > 0;
        })
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
                    value={query}
                    onInput={setQuery}
                />
                <IconButton title="Search">
                    <Search size={15} />
                </IconButton>
            </Container>
        </PopoutContainer>
    )
}
