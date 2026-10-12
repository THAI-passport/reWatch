"""reWatch wiring: skills exist with front matter, are loaded by re-workflow and listed in README; AGENTS rules present."""
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NEW_SKILLS = ("re-jieli", "re-ble-android-patterns", "re-watch-targets", "re-capture-ingestion")


def read(*p):
    return open(os.path.join(ROOT, *p), encoding="utf-8").read()


class WatchRepo(unittest.TestCase):
    def test_new_skills_have_front_matter(self):
        for n in NEW_SKILLS:
            t = read(".claude", "skills", n, "SKILL.md")
            m = re.match(r"^---\nname: (.+)\ndescription: (.+)\n---\n", t)
            self.assertTrue(m, n)
            self.assertEqual(m.group(1), n)
            self.assertGreater(len(m.group(2)), 80, n)

    def test_workflow_loads_and_readme_lists_the_skills(self):
        wf, readme, agents = read(".claude", "skills", "re-workflow", "SKILL.md"), read("README.md"), read("AGENTS.md")
        for n in NEW_SKILLS:
            self.assertIn(n, wf, n)
            self.assertIn(".claude/skills/" + n, readme, n)
            self.assertIn(n, agents, n)

    def test_agents_rules_for_watches(self):
        a = read("AGENTS.md")
        for needle in ("Software first, hardware last", "last resort", "explicit approval", "docs/SOP.md", "never by a floating",
                       "Rebuild only when necessary", "Priority platforms: Linux", "Evidence tags"):
            self.assertIn(needle, a, needle)
        self.assertIn("reWatch", a.splitlines()[0])

    def test_docs_exist_and_cross_link(self):
        self.assertIn("docs/FROM-REBEAMBOX.md", read("README.md"))
        self.assertIn("github.com/THAI-passport/reBeamBox", read("docs", "FROM-REBEAMBOX.md"))
        sop = read("docs", "SOP.md")
        for needle in ("Packer and protection triage", "Pinning", "--max-heap", "btcap"):
            self.assertIn(needle, sop.replace("Pin by exact", "Pinning"), needle)

    def test_benchmark_note_has_prompt_and_no_research(self):
        b = read("targets", "_benchmark", "BENCHMARK.md")
        self.assertIn("T900 and C900", b)
        self.assertIn("No T900 or C900 research", b)
        self.assertTrue(os.path.exists(os.path.join(ROOT, "targets", ".gitkeep")))
        self.assertEqual(sorted(os.listdir(os.path.join(ROOT, "targets", "_benchmark"))), ["BENCHMARK.md"])

    def test_no_badge_specific_values_outside_labelled_examples(self):
        for n in ("re-ble-android-patterns", "re-watch-targets", "re-capture-ingestion"):
            t = read(".claude", "skills", n, "SKILL.md")
            for bad in ("01F0", "nn20", "Nikko", "Niji"):
                self.assertNotIn(bad, t, (n, bad))
        self.assertIn("worked example", read(".claude", "skills", "re-jieli", "SKILL.md"))

    def test_watch_skills_mark_uncertainty(self):
        t = read(".claude", "skills", "re-watch-targets", "SKILL.md")
        self.assertIn("[U]", t)
        self.assertIn("[W]", t)
        self.assertIn("Verify every item", t)


if __name__ == "__main__":
    unittest.main()
