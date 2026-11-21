/** 404 page for unknown routes.
 */
import { Content, Header1, Text } from "flufi-ui/components";

import "./style.css";

export function NotFoundPage() {
    return (
        <Content class="not-found">
            <Header1>Not Found</Header1>
            <Text content="page not found :(" />
        </Content>
    )
}
