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

// BEGIN GENERATED ICONS
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
export const Cast = styled("Cast");
export const Check = styled("Check");
export const ChevronDown = styled("ChevronDown");
export const ChevronLeft = styled("ChevronLeft");
export const ChevronRight = styled("ChevronRight");
export const ChevronUp = styled("ChevronUp");
export const Circle = styled("Circle");
export const CircleAlert = styled("CircleAlert");
export const CircleCheck = styled("CircleCheck");
export const CircleDashed = styled("CircleDashed");
export const CircleHelp = styled("CircleHelp");
export const CircleX = styled("CircleX");
export const Clock = styled("Clock");
export const CloudUpload = styled("CloudUpload");
export const Code = styled("Code");
export const Coffee = styled("Coffee");
export const Compass = styled("Compass");
export const Cookie = styled("Cookie");
export const Copy = styled("Copy");
export const Database = styled("Database");
export const Disc3 = styled("Disc3");
export const Download = styled("Download");
export const Dumbbell = styled("Dumbbell");
export const Ellipsis = styled("Ellipsis");
export const ExternalLink = styled("ExternalLink");
export const EyeOff = styled("EyeOff");
export const File = styled("File");
export const FileArchive = styled("FileArchive");
export const FileCode = styled("FileCode");
export const FileQuestion = styled("FileQuestion");
export const FileSymlink = styled("FileSymlink");
export const FileText = styled("FileText");
export const Film = styled("Film");
export const Flame = styled("Flame");
export const Flower = styled("Flower");
export const Folder = styled("Folder");
export const FolderPlus = styled("FolderPlus");
export const GripVertical = styled("GripVertical");
export const HardDrive = styled("HardDrive");
export const Headphones = styled("Headphones");
export const Heart = styled("Heart");
export const Home = styled("House");
export const House = styled("House");
export const Image = styled("Image");
export const Inbox = styled("Inbox");
export const Info = styled("Info");
export const Key = styled("Key");
export const KeyRound = styled("KeyRound");
export const Library = styled("Library");
export const Link = styled("Link");
export const Link2 = styled("Link2");
export const List = styled("List");
export const ListFilter = styled("ListFilter");
export const ListMusic = styled("ListMusic");
export const ListPlus = styled("ListPlus");
export const Loader2 = styled("Loader2");
export const LoaderCircle = styled("LoaderCircle");
export const LocateFixed = styled("LocateFixed");
export const Lock = styled("Lock");
export const LogIn = styled("LogIn");
export const LogOut = styled("LogOut");
export const Mail = styled("Mail");
export const Menu = styled("Menu");
export const MessageCircle = styled("MessageCircle");
export const MicVocal = styled("MicVocal");
export const Monitor = styled("Monitor");
export const MonitorSmartphone = styled("MonitorSmartphone");
export const Moon = styled("Moon");
export const MoreHorizontal = styled("Ellipsis");
export const Music = styled("Music");
export const Music2 = styled("Music2");
export const MusicNote = styled("Music");
export const Palette = styled("Palette");
export const PanelLeftClose = styled("PanelLeftClose");
export const PanelLeftOpen = styled("PanelLeftOpen");
export const Pause = styled("Pause");
export const Pencil = styled("Pencil");
export const Pentagon = styled("Pentagon");
export const PictureInPicture2 = styled("PictureInPicture2");
export const Play = styled("Play");
export const Plus = styled("Plus");
export const Radio = styled("Radio");
export const RefreshCw = styled("RefreshCw");
export const Repeat = styled("Repeat");
export const Repeat1 = styled("Repeat1");
export const RotateCcw = styled("RotateCcw");
export const Save = styled("Save");
export const ScanLine = styled("ScanLine");
export const Search = styled("Search");
export const Send = styled("Send");
export const Server = styled("Server");
export const Settings = styled("Settings");
export const Shield = styled("Shield");
export const ShieldAlert = styled("ShieldAlert");
export const ShieldCheck = styled("ShieldCheck");
export const Shuffle = styled("Shuffle");
export const SkipBack = styled("SkipBack");
export const SkipForward = styled("SkipForward");
export const Smartphone = styled("Smartphone");
export const Sparkles = styled("Sparkles");
export const Squircle = styled("Squircle");
export const Star = styled("Star");
export const Terminal = styled("Terminal");
export const Trash = styled("Trash2");
export const Trash2 = styled("Trash2");
export const Type = styled("Type");
export const Unlink = styled("Unlink");
export const Upload = styled("Upload");
export const User = styled("UserRound");
export const UserRound = styled("UserRound");
export const Volume1 = styled("Volume1");
export const Volume2 = styled("Volume2");
export const VolumeX = styled("VolumeX");
export const Wifi = styled("Wifi");
export const WifiOff = styled("WifiOff");
export const X = styled("X");
export const Zap = styled("Zap");
// END GENERATED ICONS
