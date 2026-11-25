/* Shared Lucide registry for the web client.
 *
 * vite.config.ts and tsconfig.app.json alias the bare `lucide-preact` specifier
 * here so app icons and flufi-ui's internal icons all pick up the saved icon
 * width/fill preference. The runtime import deliberately uses a relative path
 * to avoid the alias resolving back into this module.
 */
// @ts-ignore the package ships its types at ../../node_modules/lucide-preact/dist/lucide-preact.d.ts
import * as Base from "../../node_modules/lucide-preact/dist/esm/lucide-preact.mjs";
import { iconFilled, iconStroke } from "./prefs";
import { lucideStrokeWidth } from "./theme";

export type {
    LucideIcon, LucideProps,
} from "../../node_modules/lucide-preact/dist/lucide-preact";
import type { LucideIcon } from "../../node_modules/lucide-preact/dist/lucide-preact";

/** Wrap a Lucide component so its stroke follows the preference and its size. */
function styled(name: string): LucideIcon {
    const BaseIcon = (Base as unknown as Record<string, LucideIcon>)[name];
    if (!BaseIcon) throw new Error(`Unknown Lucide icon: ${name}`);
    return props => {
        const requested = Number(props.size ?? props.width ?? 24);
        const size = Number.isFinite(requested) && requested > 0 ? requested : 24;
        const cls = [props.class, iconFilled.value ? "icon-filled" : ""]
            .filter(Boolean)
            .join(" ");
        return (
            <BaseIcon
                {...props}
                class={cls}
                strokeWidth={props.strokeWidth ?? lucideStrokeWidth(iconStroke.value, size)}
            />
        );
    };
}

export const AArrowDown = styled("AArrowDown");
export const AArrowUp = styled("AArrowUp");
export const ArrowDownUp = styled("ArrowDownUp");
export const AudioLines = styled("AudioLines");
export const AudioWaveform = styled("AudioWaveform");
export const Ban = styled("Ban");
export const Binary = styled("Binary");
export const BookOpen = styled("BookOpen");
export const Braces = styled("Braces");
export const Calendar = styled("Calendar");
export const Check = styled("Check");
export const ChevronDown = styled("ChevronDown");
export const ChevronLeft = styled("ChevronLeft");
export const ChevronRight = styled("ChevronRight");
export const Circle = styled("Circle");
export const CircleCheck = styled("CircleCheck");
export const CircleDashed = styled("CircleDashed");
export const CloudUpload = styled("CloudUpload");
export const Code = styled("Code");
export const Copy = styled("Copy");
export const Database = styled("Database");
export const Disc3 = styled("Disc3");
export const Download = styled("Download");
export const ExternalLink = styled("ExternalLink");
export const File = styled("File");
export const FileArchive = styled("FileArchive");
export const FileCode = styled("FileCode");
export const FileQuestion = styled("FileQuestion");
export const FileSymlink = styled("FileSymlink");
export const FileText = styled("FileText");
export const Film = styled("Film");
export const Folder = styled("Folder");
export const Headphones = styled("Headphones");
export const Heart = styled("Heart");
export const Home = styled("Home");
export const Image = styled("Image");
export const Inbox = styled("Inbox");
export const Info = styled("Info");
export const KeyRound = styled("KeyRound");
export const Link2 = styled("Link2");
export const ListFilter = styled("ListFilter");
export const ListMusic = styled("ListMusic");
export const ListPlus = styled("ListPlus");
export const Loader2 = styled("Loader2");
export const LocateFixed = styled("LocateFixed");
export const LogOut = styled("LogOut");
export const Mail = styled("Mail");
export const Menu = styled("Menu");
export const MicVocal = styled("MicVocal");
export const MonitorSmartphone = styled("MonitorSmartphone");
export const Music = styled("Music");
export const Music2 = styled("Music2");
export const PanelLeftClose = styled("PanelLeftClose");
export const PanelLeftOpen = styled("PanelLeftOpen");
export const Pause = styled("Pause");
export const Pencil = styled("Pencil");
export const Play = styled("Play");
export const Plus = styled("Plus");
export const Radio = styled("Radio");
export const RefreshCw = styled("RefreshCw");
export const Repeat = styled("Repeat");
export const RotateCcw = styled("RotateCcw");
export const Save = styled("Save");
export const ScanLine = styled("ScanLine");
export const Search = styled("Search");
export const Send = styled("Send");
export const Settings = styled("Settings");
export const ShieldCheck = styled("ShieldCheck");
export const Shuffle = styled("Shuffle");
export const SkipBack = styled("SkipBack");
export const SkipForward = styled("SkipForward");
export const Smartphone = styled("Smartphone");
export const Sparkles = styled("Sparkles");
export const Terminal = styled("Terminal");
export const Trash2 = styled("Trash2");
export const Type = styled("Type");
export const Unlink = styled("Unlink");
export const Upload = styled("Upload");
export const UserRound = styled("UserRound");
export const Volume2 = styled("Volume2");
export const VolumeX = styled("VolumeX");
export const WifiOff = styled("WifiOff");
export const X = styled("X");
