export const ICON_PATHS = {
  "arrow-left": '<path d="M19 12.4 C 14 11.7, 9.5 12.3, 5 12"/><path d="M11 6 L5 12 L11 18"/>',
  "arrow-right": '<path d="M5 12.4 C 10 11.7, 14.5 12.3, 19 12"/><path d="M13 6 L19 12 L13 18"/>',
  map: '<path d="M3 6.5 L9 4 L15 6.5 L21 4 V17.5 L15 20 L9 17.5 L3 20 Z"/><path d="M9 4 V17.5"/><path d="M15 6.5 V20"/>',
  text: '<path d="M4 6 H20"/><path d="M4 12 H20"/><path d="M4 18 H13"/>',
  play: '<path d="M7 4.5 L19 12 L7 19.5 Z"/>',
  pause: '<path d="M8 5 V19"/><path d="M16 5 V19"/>',
  lock: '<rect x="4.5" y="10.5" width="15" height="10" rx="2.5"/><path d="M8 10.5 V7.5 a4 4 0 0 1 8 0 V10.5"/>',
  nfc: '<path d="M6 8.3 a6 6 0 0 1 0 7.4"/><path d="M9.5 6 a9.5 9.5 0 0 1 0 12"/><path d="M13 4 a12.5 12.5 0 0 1 0 16"/><path d="M16.5 2.5 a15 15 0 0 1 0 19"/>',
  qr: '<rect x="3.5" y="3.5" width="6.5" height="6.5" rx="1"/><rect x="14" y="3.5" width="6.5" height="6.5" rx="1"/><rect x="3.5" y="14" width="6.5" height="6.5" rx="1"/><path d="M14 14 H17 V17 M20.5 14 V14.01 M14 20.5 H20.5 V17"/>',
  copy: '<rect x="8.5" y="8.5" width="12" height="12" rx="2.5"/><path d="M15.5 8.5 V5.5 a2 2 0 0 0 -2 -2 H5.5 a2 2 0 0 0 -2 2 V13.5 a2 2 0 0 0 2 2 H8.5"/>',
  check: '<path d="M4.5 12.5 L9.5 17.5 L19.5 6.5"/>',
  x: '<path d="M6 6 L18 18"/><path d="M18 6 L6 18"/>',
  menu: '<path d="M4 7 H20"/><path d="M4 12 H20"/><path d="M4 17 H20"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2.5 V4.5 M12 19.5 V21.5 M2.5 12 H4.5 M19.5 12 H21.5 M5.3 5.3 L6.7 6.7 M17.3 17.3 L18.7 18.7 M5.3 18.7 L6.7 17.3 M17.3 6.7 L18.7 5.3"/>',
  moon: '<path d="M20 14.5 A8 8 0 1 1 9.5 4 A6.5 6.5 0 0 0 20 14.5 Z"/>',
  globe:
    '<circle cx="12" cy="12" r="9"/><path d="M3 12 H21"/><path d="M12 3 C 15 6, 15 18, 12 21 C 9 18, 9 6, 12 3 Z"/>',
  user: '<circle cx="12" cy="8" r="4"/><path d="M4.5 20.5 C 5.5 16.5, 8.5 14.5, 12 14.5 C 15.5 14.5, 18.5 16.5, 19.5 20.5"/>',
  logout:
    '<path d="M14 4.5 H18.5 a1.5 1.5 0 0 1 1.5 1.5 V18 a1.5 1.5 0 0 1 -1.5 1.5 H14"/><path d="M10 8 L6 12 L10 16"/><path d="M6 12 H15"/>',
  headphones:
    '<path d="M4 18 V13 a8 8 0 0 1 16 0 V18"/><rect x="3.5" y="13.5" width="4.5" height="7" rx="1.5"/><rect x="16" y="13.5" width="4.5" height="7" rx="1.5"/>',
  pin: '<path d="M12 21.5 C 7 16, 5 12.5, 5 9.5 a7 7 0 0 1 14 0 C 19 12.5, 17 16, 12 21.5 Z"/><circle cx="12" cy="9.5" r="2.5"/>',
  share:
    '<path d="M12 3.5 V15"/><path d="M7.5 7.5 L12 3.5 L16.5 7.5"/><path d="M5 12 V19 a1.5 1.5 0 0 0 1.5 1.5 H17.5 a1.5 1.5 0 0 0 1.5 -1.5 V12"/>',
  "chevron-right": '<path d="M9.5 5.5 L16 12 L9.5 18.5"/>',
  "chevron-down": '<path d="M5.5 9.5 L12 16 L18.5 9.5"/>',
  plus: '<path d="M12 5 V19"/><path d="M5 12 H19"/>',
  search: '<circle cx="11" cy="11" r="6.5"/><path d="M16 16 L20.5 20.5"/>',
  edit: '<path d="M15.5 4.5 L19.5 8.5 L8.5 19.5 L4 20 L4.5 15.5 Z"/><path d="M13.5 6.5 L17.5 10.5"/>',
  trash:
    '<path d="M4 7 H20"/><path d="M9.5 7 V4.5 H14.5 V7"/><path d="M6 7 L7 20 H17 L18 7"/><path d="M10 11 V16 M14 11 V16"/>',
  upload:
    '<path d="M12 15.5 V4"/><path d="M7.5 8.5 L12 4 L16.5 8.5"/><path d="M4.5 15 V19 a1.5 1.5 0 0 0 1.5 1.5 H18 a1.5 1.5 0 0 0 1.5 -1.5 V15"/>',
  download:
    '<path d="M12 4 V15.5"/><path d="M7.5 11 L12 15.5 L16.5 11"/><path d="M4.5 15 V19 a1.5 1.5 0 0 0 1.5 1.5 H18 a1.5 1.5 0 0 0 1.5 -1.5 V15"/>',
  eye: '<path d="M2.5 12 C 5 7, 8.5 5, 12 5 C 15.5 5, 19 7, 21.5 12 C 19 17, 15.5 19, 12 19 C 8.5 19, 5 17, 2.5 12 Z"/><circle cx="12" cy="12" r="3"/>',
  chart: '<path d="M4 4 V20 H20"/><path d="M7.5 15 L11 10.5 L14 13 L19 7"/>',
  route:
    '<circle cx="6" cy="18" r="2.5"/><circle cx="18" cy="6" r="2.5"/><path d="M8.5 18 H15 a3 3 0 0 0 0 -6 H9 a3 3 0 0 1 0 -6 H15.5"/>',
  list: '<path d="M9 6 H20 M9 12 H20 M9 18 H20"/><path d="M4.5 6 H5 M4.5 12 H5 M4.5 18 H5"/>',
  gift: '<rect x="3.5" y="8" width="17" height="4" rx="1"/><path d="M5 12 V20 H19 V12"/><path d="M12 8 V20"/><path d="M12 8 C 9 8, 7 7, 7 5.3 C 7 3.5, 9.5 3.5, 12 8 C 14.5 3.5, 17 3.5, 17 5.3 C 17 7, 15 8, 12 8"/>',
  mail: '<rect x="3" y="5.5" width="18" height="13" rx="2"/><path d="M3.5 7 L12 13 L20.5 7"/>',
  alert: '<circle cx="12" cy="12" r="9"/><path d="M12 7.5 V13"/><path d="M12 16.5 V16.6"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11 V16.5"/><path d="M12 7.5 V7.6"/>',
  settings:
    '<circle cx="12" cy="12" r="3"/><path d="M12 2.5 V5 M12 19 V21.5 M2.5 12 H5 M19 12 H21.5 M5.3 5.3 L7.1 7.1 M16.9 16.9 L18.7 18.7 M5.3 18.7 L7.1 16.9 M16.9 7.1 L18.7 5.3"/>',
  image:
    '<rect x="3.5" y="4.5" width="17" height="15" rx="2"/><circle cx="9" cy="10" r="1.8"/><path d="M4 18 L10 12.5 L14 16 L16.5 13.5 L20 17"/>',
  grip: '<circle cx="9" cy="6" r=".8"/><circle cx="15" cy="6" r=".8"/><circle cx="9" cy="12" r=".8"/><circle cx="15" cy="12" r=".8"/><circle cx="9" cy="18" r=".8"/><circle cx="15" cy="18" r=".8"/>',
  wand: '<path d="M4 20 L14 10"/><path d="M15 3.5 V6.5 M13.5 5 H16.5 M19 8.5 V11.5 M17.5 10 H20.5"/>',
  home: '<path d="M3.5 11 L12 4 L20.5 11"/><path d="M6 9.5 V20 H18 V9.5"/><path d="M10 20 V14.5 H14 V20"/>',
  sparkle:
    '<path d="M12 3 C 12.8 8.5, 15.5 11.2, 21 12 C 15.5 12.8, 12.8 15.5, 12 21 C 11.2 15.5, 8.5 12.8, 3 12 C 8.5 11.2, 11.2 8.5, 12 3 Z"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7 V12 L15.5 14"/>',
  filter: '<path d="M4 5.5 H20 L14 13 V19 L10 20.5 V13 Z"/>',
} as const;

export type IconName = keyof typeof ICON_PATHS;
