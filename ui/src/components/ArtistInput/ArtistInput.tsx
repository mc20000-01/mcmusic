/** Artist picker used by the upload/edit forms.
 */
import { useSignal, type Signal } from "@preact/signals";
import { SelectBox } from "flufi-ui/components";
import {
    isSignal,
    loaded,
    maybeLoadedMap,
    notLoaded,
    type MaybeLoaded,
    type Option,
    type Signalish,
    type Uuid
} from "flufi-ui/types";
import { useEffect, useState } from "preact/hooks";
import type { Artist } from "../../common/net/types";
import { API } from "../../common/net/api";

export function ArtistInput(props: {
    value?: Signalish<Option<Uuid>>,
    onChange?: (value: Option<Uuid>) => void,
    dirty?: Signal<boolean>,
    class?: string,
}) {
    const [list, setList] = useState<MaybeLoaded<Artist[]>>(notLoaded());
    
    useEffect(() => {
        let cancelled = false;
        API.listArtists()
            .then(artists => {
                if (!cancelled)
                    setList(loaded(artists));
            })
            .catch(error => console.error("failed to load artists", error));
        return () => { cancelled = true; };
    }, []);
    
    let value: Signal<Option<Uuid>>;
    if (props.value == null)
        value = useSignal<Option<Uuid>>(null);
    else if (isSignal(props.value))
        value = props.value as Signal<Option<Uuid>>;
    else
        value = useSignal(props.value as Option<Uuid>);
    
    return (
        <SelectBox
            value={value as any}
            onChange={props.onChange as any}
            dirty={props.dirty}
            options={
                maybeLoadedMap(list,
                    (list) => list.map(a => ({
                        value: a.uuid,
                        label: a.name
                    }))
                ) as any
            }
        />
    )
}
