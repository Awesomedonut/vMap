# Publicly Available Current Map Tools

Market research as of August 2026. Two parts: (1) a survey of the existing fictional map-making market, and (2) a deep-dive into whether anything close to the vMap pitch ("Google Maps for fictional worlds") already exists.

---

## Part 1: The Existing Market

### Market leaders (general-purpose fantasy map editors)

| Tool | Platform / Model | Price | Positioning |
|---|---|---|---|
| [Inkarnate](https://inkarnate.com) | Web, subscription | Free tier; Pro $5/mo or $25/yr | Market leader by popularity. All-in-one: world, regional, city, battle, and isometric maps in multiple art styles. Huge asset library; Pro unlocks hi-res export and commercial use. |
| [Wonderdraft](https://www.wonderdraft.net) | Desktop, one-time | ~$30 | The solo worldbuilder's favorite for hand-drawn-style overland/world maps. Offline, local files, no subscription. |
| [Dungeondraft](https://dungeondraft.net) | Desktop, one-time | ~$30 | Wonderdraft's sibling for dungeons/battlemaps. Its export format is the de facto standard for importing maps into Foundry VTT. |
| [Campaign Cartographer 3+](https://www.profantasy.com) | Desktop (ProFantasy) | ~$40 base + add-ons | The legacy CAD-style veteran (est. 1993). Most powerful, most map styles, steepest learning curve; widely seen as dated. |
| [Dungeon Alchemist](https://store.steampowered.com/app/1588530/Dungeon_Alchemist/) | Steam, one-time | $44.99 | AI-assisted: draw a room shape, pick a theme, and it auto-furnishes in 3D; exports 2D VTT-ready maps. 6000+ objects; full release planned late 2026. |

### Battlemap / VTT-focused tools

- **[Dungeon Scrawl](https://www.dungeonscrawl.com)** (owned by Roll20) — browser-based dungeon sketching; ~99% of features free, Pro subscription for advanced features.
- **[DungeonFog](https://www.dungeonfog.com)** — online battlemap editor; pioneered the Universal VTT export format (walls, doors, lighting → Foundry etc.).
- **[Arkenforge](https://arkenforge.com)** — 3D map builder with dynamic lighting, popular for in-person digital-table play.
- **[D&D Beyond Maps](https://www.dndbeyond.com)** — after Wizards killed the Sigil VTT (servers shut down October 2026), Maps became free to all D&D Beyond users and is being invested in heavily.

### Free / procedural generators

- **[Azgaar's Fantasy Map Generator](https://azgaar.github.io/Fantasy-Map-Generator/)** — free, open-source; procedurally generates full worlds with biomes, cultures, religions, states, and borders. The reference point for procedural world generation.
- **[Watabou's Procgen Arcana](https://watabou.github.io/)** — free generators for medieval cities, villages, and dungeons; integrates with Azgaar (generate a city from an Azgaar settlement).
- **[Worldographer 2025](https://store.inkwellideas.com)** — hex-map oriented (world/kingdom/city/dungeon); free, ~$30 to unlock power features.

### Worldbuilding platforms with map features

- **[World Anvil](https://www.worldanvil.com/features/maps)**, **[LegendKeeper](https://www.legendkeeper.com)**, **[Kanka](https://kanka.io)** (open-source, self-hostable), and **Campfire** bundle interactive maps (pins, layers, linked lore) into broader lore-management platforms. They consume maps made elsewhere rather than compete on map authoring.

### Market trends

1. **AI generation is the active frontier** — Dungeon Alchemist's auto-furnishing is the commercial success story; pure AI battlemap generators are emerging.
2. **Business model split** — subscriptions (Inkarnate, Dungeon Scrawl Pro) vs. one-time purchases (Wonderdraft, Dungeon Alchemist).
3. **VTT interop is table stakes** — Universal VTT export and Foundry importers are now expected.
4. **Consolidation** — Roll20 acquired Dungeon Scrawl; Wizards killed Sigil and pivoted to free D&D Beyond Maps.

**The common thread: every one of these tools ultimately produces a static 2D image.** None of them makes the world itself navigable.

---

## Part 2: Does Anything Like vMap Already Exist?

Deep search for products combining: navigable Google-Maps-style exploration + hosted/shareable worlds + procedural generation + distance/travel calculation + street view. **No single product does all of this.** But several do pieces of it:

### Closest overlaps — watch these

| Product | What it does | Overlap with vMap | Gap |
|---|---|---|---|
| **[fictionalmaps.com](https://fictionalmaps.com/)** | Upload a map image → it auto-generates a zoomable, shareable web map with markers, search box, scale bar, zoom-dependent marker visibility. | The closest direct match to "hosted, Google-Maps-like fictional maps." | Image-upload only — no procedural generation, no routing/travel time, no street view; still under active development with features missing. |
| **[LegendKeeper](https://www.legendkeeper.com/the-new-legendkeeper-map-tool-is-here/)** | Worldbuilding wiki with a rebuilt map tool: regions, paths, labels, distance calibration ("X miles between these two points"), and a **Navigation Mode** — pick two pins, get distance, route, and travel time at a given speed. Zoom-dependent layers. | Has the distance/travel-time feature almost exactly as pitched. | Maps are uploaded images inside a private wiki — no public hosted world sites, no street view. No procedural generation today (early experimental generators were hidden), but it's explicitly on their roadmap to return. |
| **[World Anvil Maps](https://www.worldanvil.com/features/maps)** | Interactive maps with pins, layers (tectonics, climate, politics), map-to-map linking (world → city → building), spoiler-controlled visibility, published to readers. | Hosted, explorable, layered maps tied to lore. | Built around uploaded images; a distance-measure tool is still just a community suggestion; no generation, no navigation. |
| **[OpenGeofiction](https://www.opengeofiction.net/)** | A collaborative fictional Earth-sized world built on the actual OpenStreetMap software stack — real slippy-map tiles, real map editors, thousands of contributors since 2013. | Proof that "OSM/Google Maps tech for a fictional world" works and sustains a community. | One shared modern-day realistic world (no fantasy elements allowed); not a platform where anyone can host their own world. |
| **[Azgaar's FMG](https://azgaar.github.io/Fantasy-Map-Generator/)** | Procedural world generation with editable states, cultures, routes, and rulers; interactive in-browser with zoom and measurement tools. | The procedural-generation half of the pitch, free and open source. | A single-page tool, not a hosted platform; no per-world sites, no street view, limited navigation. |

### Fan-made proofs of demand

These show exactly the audience described in the pitch already building one-off versions by hand:

- **[LotrProject](http://lotrproject.com/map/)** — interactive Middle-earth map with paths, events, and a [time/distance analysis](http://lotrproject.com/timedistance/) of Frodo's and Bilbo's journeys, day by day.
- **[Quartermaester](https://quartermaester.info/)** — interactive Westeros map with character paths over time and spoiler controls.
- **[Google's Middle-earth experiment](https://fantasy-faction.com/2013/google-middle-earth-interactive-map)** (2013) — a Chrome experiment with a Street-View-like ground-level walk through Middle-earth. Google itself validated the street-view-for-fantasy concept, then abandoned it.
- **[ArdaCraft](https://www.ardacraft.me/map/middle-earth-interactive-map)** — Minecraft recreation of Middle-earth with its own interactive web map; effectively street view via the game client.
- **Guild Wars 2 / game wikis** — [Tyria on Google Maps tech](https://googlemapsmania.blogspot.com/2012/08/the-fantasy-world-tyria-on-google-maps.html): game communities routinely rebuild their game worlds as slippy maps.

Every one of these was hand-built by fans for a single franchise. vMap would be the platform that makes this a product anyone can have.

### Adjacent / experimental

- **[Project Deios](https://www.kickstarter.com/projects/dungeonfog/project-deios-dungeonfog-mapmaker-suite-for-worldbuilders)** (DungeonFog, Kickstarter) — a "mapmaker suite" linking battle, city, and world maps in one system. Nearest thing to multi-scale world coherence from an incumbent, but still an editor, not a hosted navigable platform.
- **[Undiscovered Worlds](https://github.com/JonathanCRH/Undiscovered_Worlds)** — open-source procedural planet generator with explorable spherical globes.
- **[Songs of the Eons](https://demiansky.itch.io/songs-of-the-eons)** — sandbox fantasy world simulator evolving ecology, economics, and societies over eons.
- **[World Orogen](https://www.orogen.studio/)** — procedural planet generator focused on realistic terrain.

### Gap analysis — where vMap is unique

No existing product combines all five pillars:

| Capability | Who has it today | Hosted platform? | Procedural? | Navigation/travel time? | Street view? |
|---|---|---|---|---|---|
| Zoomable hosted fictional maps | fictionalmaps.com, World Anvil | partial | ✗ | ✗ | ✗ |
| Distance + travel time | LegendKeeper, LotrProject | ✗ | ✗ | ✓ | ✗ |
| Procedural world generation | Azgaar, Undiscovered Worlds | ✗ | ✓ | ✗ | ✗ |
| Real map-stack fictional world | OpenGeofiction | single world | ✗ | partial | ✗ |
| Street-level fictional exploration | Google's 2013 experiment, ArdaCraft | ✗ | ✗ | ✗ | ✓ (one-off) |

The unclaimed position: **a platform where any creator gets a procedurally generated (or imported), fully navigable world at their own address** — the Tumblr model applied to worlds instead of blogs. The pieces have each been proven viable separately; nobody has assembled them.

---

*Sources: [LegendKeeper's map-making software review](https://www.legendkeeper.com/map-making-software/), [TTRPG Stack](https://www.ttrpgstack.com/tools/inkarnate/), [Dungeon Alchemist press kit](https://www.dungeonalchemist.com/presskit), [Sigil sunset FAQ](https://dndbeyond-support.wizards.com/hc/en-us/articles/42550438974868-Sigil-Sunset-FAQ), [Geoawesome on fictional maps](https://geoawesome.com/fictional-maps-crafting-online-fantasy-worlds/), [OpenGeofiction About](https://wiki.opengeofiction.net/index.php/OpenGeofiction:About), [World Anvil map features](https://www.worldanvil.com/features/maps), [LegendKeeper map tool announcement](https://www.legendkeeper.com/the-new-legendkeeper-map-tool-is-here/), [fictionalmaps.com](https://fictionalmaps.com/), [char-gen AI battlemap roundup](https://char-gen.com/blogs/best-ai-battlemap-generators-dnd-2026).*
