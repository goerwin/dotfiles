import { div, View } from "gpui-kit";
import { h_flex } from "gpui-base";
import { appHome, checking, exec, theme, window } from "herdr";

const refreshInterval = 60_000;
const providers = [
  { id: "gocode", name: "Gocode", shellOptions: ["-f"], timeout: 20_000 },
  { id: "cursor", name: "Cursor", shellOptions: [], timeout: 12_000 },
];

/** @param {number} amount */
function dollars(amount) {
  return `$${amount.toFixed(2).replace(/\.?0+$/, "")}`;
}

/**
 * @param {string} name
 * @param {{spend: number, max_budget: number | null}} budget
 */
function budgetLabel(name, { spend, max_budget }) {
  return `${name} ${dollars(spend)}/${max_budget === null ? "—" : dollars(max_budget)}`;
}

export default class GoDaddyAI extends View {
  init() {
    this.budgets = providers.map((provider) => ({
      ...provider,
      label: `${provider.name} checking…`,
      lastBudget: "",
      failed: false,
    }));
    this.waiting = false;
    this.refreshing = false;
  }

  refresh(cx) {
    if (checking() || !window()?.visible || this.waiting || this.refreshing) return;

    this.waiting = true;
    cx.timer.after(refreshInterval, (cx) => {
      this.waiting = false;
      this.refresh(cx);
    });
    this.refreshing = true;
    const script = `${appHome()}/mods/godaddy-ai/query.zsh`;
    cx.spawn(async (cx) => {
      try {
        await Promise.all(this.budgets.map(async (budget) => {
          let unavailable = `${budget.name} unavailable`;
          try {
            const result = await exec(
              "/bin/zsh",
              [...budget.shellOptions, script, budget.id],
              { timeout: budget.timeout },
            );
            if (result.code === 78) unavailable = `${budget.name} credentials unavailable`;
            if (result.code !== 0) throw new Error(unavailable);

            budget.lastBudget = budgetLabel(budget.name, JSON.parse(result.stdout));
            budget.label = budget.lastBudget;
            budget.failed = false;
          } catch {
            budget.failed = true;
            budget.label = budget.lastBudget ? `${budget.lastBudget} (stale)` : unavailable;
          }
          cx.notify();
        }));
      } finally {
        this.refreshing = false;
      }
    });
  }

  render(cx) {
    this.refresh(cx);
    const colors = theme();
    const label = this.budgets.map((budget) => budget.label).join(" - ");
    return h_flex().size_full().justify_end().items_center().px(14)
      .bg(colors.chrome).border_t(1).border_color(colors.border)
      .child(div().id("budget").text_size(11.8)
        .text_color(this.budgets.every((budget) => budget.failed) ? colors.dim : colors.muted)
        .truncate().tooltip(label).child(label));
  }
}
