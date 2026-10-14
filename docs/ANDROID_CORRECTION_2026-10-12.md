# Android correction checkpoint — 2026-10-12

This correction pass addresses the supplied screenshots and is applied to the combined 12-mod candidate.

- Waystone is now a placeable custom block with a block geometry loader path, explicit block item/icon, localized name, and a non-spawnable legacy entity retained only for loaded-world migration.
- Generated custom items now receive explicit `minecraft:icon` components and `en_US`/`pt_BR` localization. The final static check found zero item icon references missing from the atlas.
- Aether rings use two persisted virtual accessory slots independent of native offhand. A ring left in offhand by the previous prototype is migrated once.
- Ice and Fire/Alex's Caves support icons are present for dragon meals, flute, iron armor, eggs, scales, and Serene Salad.

Local evidence for the candidate: 26 Python tests passed, 36 Node tests passed, all final behavior scripts passed `node --check`, nested ZIP integrity passed, 19 entities, 352 blocks, and 765 items. Android rendering, UI, Beta/Upcoming Creator Features, performance, and existing-world migration still require device verification.
