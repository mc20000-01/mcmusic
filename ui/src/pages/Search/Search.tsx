/** Full-page search. The topbar popout is for quick jumps; this view groups
 *  every result by type so a broad query is still browsable.
 */
import { useEffect, useState } from "preact/hooks";
import { useLocation } from "preact-iso";
import { Container, Content, Header2, Header3, Input, Loading, Text } from "flufi-ui/components";
import { Search as SearchIcon } from "lucide-preact";
import { API } from "../../common/net/api";
import type { SearchItem } from "../../common/net/types";
import { SearchItemElem } from "../../components/SearchBar/SearchItem";

import "./style.css";

type Group = "artist" | "set" | "track";
const GROUPS: [Group, string][] = [
    ["artist", "Artists"],
    ["set", "Albums"],
    ["track", "Tracks"],
];

export function SearchPage() {
    const loc = useLocation();
    const query = String(loc.query.q ?? "");
    const [text, setText] = useState(query);
    const [items, setItems] = useState<SearchItem[] | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => { setText(query); }, [query]);

    useEffect(() => {
        let cancelled = false;
        if (!query.trim()) {
            setItems([]);
            return;
        }
        setItems(null);
        setError(null);
        API.search(query)
            .then(r => { if (!cancelled) setItems(r); })
            .catch(e => {
                if (!cancelled) { setError(String(e)); setItems([]); }
            });
        return () => { cancelled = true; };
    }, [query]);

    function submit(value: string) {
        const q = value.trim();
        loc.route(q ? `/search?q=${encodeURIComponent(q)}` : "/search");
    }

    return (
        <Content class="search-page">
            <Container extra_gap>
                <Header2>Search</Header2>
                <Container horizontal centered_y class="search-page-field">
                    <SearchIcon size={18} />
                    <Input
                        value={text}
                        placeholder="Songs, albums, artists…"
                        onInput={setText}
                        onEnter={submit}
                    />
                </Container>
                {error && <Text class="error" content={error} />}
                {!query ? (
                    <Text dim content="Type a query above, or press / anywhere to search." />
                ) : (
                    <Loading loaded={items != null}>
                        {() => {
                            const found = items ?? [];
                            if (found.length === 0) {
                                return <Text dim content={`No results for “${query}”.`} />;
                            }
                            return (
                                <Container extra_gap>
                                    {GROUPS.map(([kind, label]) => {
                                        const group = found.filter(i => i.type === kind);
                                        if (group.length === 0) return null;
                                        return (
                                            <Container key={kind}>
                                                <Header3>{label}</Header3>
                                                <Container vertical class="search-results">
                                                    {group.map(i => (
                                                        <SearchItemElem key={`${i.type}-${i.uuid}`} item={i} />
                                                    ))}
                                                </Container>
                                            </Container>
                                        );
                                    })}
                                </Container>
                            );
                        }}
                    </Loading>
                )}
            </Container>
        </Content>
    );
}
