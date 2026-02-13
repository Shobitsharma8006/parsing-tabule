


from app.parsers.base_parser import BaseParser


class DashboardStoryParser(BaseParser):
    """
    Parses Dashboards and Stories separately from Tableau XML
    """

    def parse(self) -> dict:
        self.log_start()

        dashboards = self._parse_dashboards()
        stories = self._parse_stories()

        self.log_complete({
            "dashboard_count": len(dashboards),
            "story_count": len(stories)
        })

        return {
            "dashboards": dashboards,
            "stories": stories
        }

    # ==================================================
    # DASHBOARDS (EXISTING LOGIC)
    # ==================================================
    def _parse_dashboards(self):
        dashboards = []

        for dash in self.root.findall(".//dashboard"):
            name = dash.attrib.get("name")

            layout = dash.attrib.get("layout", "tiled")
            objects = []

            for zone in dash.findall(".//zone"):
                objects.append({
                    "zone_id": zone.attrib.get("id"),
                    "type": zone.attrib.get("type"),
                    "worksheet": zone.attrib.get("worksheet"),
                    "parent_zone": zone.attrib.get("parent-zone"),
                    "position": {
                        "x": int(zone.attrib.get("x", 0)),
                        "y": int(zone.attrib.get("y", 0)),
                        "width": int(zone.attrib.get("w", 0)),
                        "height": int(zone.attrib.get("h", 0)),
                    }
                })

            dashboards.append({
                "name": name,
                "layout": layout,
                "objects": objects,
                "actions": []  # actions parsed elsewhere
            })

        return dashboards

    # ==================================================
    # STORIES (NEW – THIS WAS MISSING)
    # ==================================================
    def _parse_stories(self):
        stories = []

        for story in self.root.findall(".//story"):
            story_name = story.attrib.get("name")

            points = []

            for sp in story.findall(".//story-point"):
                point_name = sp.attrib.get("name")

                # Story point can reference dashboard OR worksheet
                dash_ref = sp.find(".//dashboard")
                sheet_ref = sp.find(".//worksheet")

                if dash_ref is not None:
                    points.append({
                        "name": point_name,
                        "target_type": "dashboard",
                        "target_name": dash_ref.attrib.get("name")
                    })
                elif sheet_ref is not None:
                    points.append({
                        "name": point_name,
                        "target_type": "worksheet",
                        "target_name": sheet_ref.attrib.get("name")
                    })

            stories.append({
                "name": story_name,
                "story_points": points
            })

        return stories












