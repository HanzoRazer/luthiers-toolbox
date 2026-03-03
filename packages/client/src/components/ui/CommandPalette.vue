<template>
  <Teleport to="body">
    <Transition name="palette">
      <div
        v-if="isOpen"
        class="command-palette-overlay"
        @click.self="close"
      >
        <div
          class="command-palette"
          role="dialog"
          aria-modal="true"
          aria-label="Command palette"
        >
          <!-- Search input -->
          <div class="palette-header">
            <span class="palette-icon">🔍</span>
            <input
              ref="inputRef"
              v-model="query"
              type="text"
              class="palette-input"
              placeholder="Type a command or search..."
              autocomplete="off"
              spellcheck="false"
              @keydown.stop
            >
            <kbd class="palette-shortcut">ESC</kbd>
          </div>

          <!-- Results -->
          <div
            class="palette-results"
            role="listbox"
          >
            <template v-if="filteredCommands.length === 0">
              <div class="palette-empty">
                No commands found
              </div>
            </template>

            <template v-else>
              <template
                v-for="(commands, category) in groupedCommands"
                :key="category"
              >
                <div class="palette-category">
                  {{ categoryLabel(category) }}
                </div>
                <button
                  v-for="cmd in commands"
                  :key="cmd.id"
                  class="palette-item"
                  :class="{ selected: isSelected(cmd) }"
                  role="option"
                  :aria-selected="isSelected(cmd)"
                  @click="executeCommand(cmd)"
                  @mouseenter="hoverIndex(cmd)"
                >
                  <span class="item-icon">{{ cmd.icon || '→' }}</span>
                  <span class="item-label">{{ cmd.label }}</span>
                  <span
                    v-if="cmd.shortcut"
                    class="item-shortcut"
                  >
                    <kbd>{{ cmd.shortcut }}</kbd>
                  </span>
                </button>
              </template>
            </template>
          </div>

          <!-- Footer hint -->
          <div class="palette-footer">
            <span><kbd>↑↓</kbd> navigate</span>
            <span><kbd>↵</kbd> select</span>
            <span><kbd>esc</kbd> close</span>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from "vue";
import { useCommandPalette, type Command } from "@/composables/useCommandPalette";

const {
  isOpen,
  query,
  selectedIndex,
  filteredCommands,
  groupedCommands,
  close,
  executeCommand,
} = useCommandPalette();

const inputRef = ref<HTMLInputElement | null>(null);

// Focus input when opened
watch(isOpen, (open) => {
  if (open) {
    nextTick(() => {
      inputRef.value?.focus();
    });
  }
});

// Reset selection when query changes
watch(query, () => {
  selectedIndex.value = 0;
});

function categoryLabel(category: string): string {
  const labels: Record<string, string> = {
    recent: "Recent",
    navigation: "Navigation",
    tools: "Tools & Labs",
    actions: "Actions",
    business: "Business",
  };
  return labels[category] || category;
}

function isSelected(cmd: Command): boolean {
  const idx = filteredCommands.value.findIndex((c) => c.id === cmd.id);
  return idx === selectedIndex.value;
}

function hoverIndex(cmd: Command): void {
  const idx = filteredCommands.value.findIndex((c) => c.id === cmd.id);
  if (idx >= 0) {
    selectedIndex.value = idx;
  }
}
</script>

<style scoped>
.command-palette-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 15vh;
  z-index: 9999;
  backdrop-filter: blur(2px);
}

.command-palette {
  width: 100%;
  max-width: 560px;
  background: var(--color-surface, #fff);
  border-radius: 12px;
  box-shadow:
    0 25px 50px -12px rgba(0, 0, 0, 0.25),
    0 0 0 1px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.palette-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border-bottom: 1px solid var(--color-border, #e5e7eb);
}

.palette-icon {
  font-size: 18px;
  opacity: 0.5;
}

.palette-input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 16px;
  background: transparent;
  color: var(--color-text, #111);
}

.palette-input::placeholder {
  color: var(--color-text-muted, #9ca3af);
}

.palette-shortcut {
  padding: 4px 8px;
  font-size: 11px;
  font-family: inherit;
  background: var(--color-muted, #f3f4f6);
  border-radius: 4px;
  color: var(--color-text-muted, #6b7280);
}

.palette-results {
  max-height: 400px;
  overflow-y: auto;
  padding: 8px;
}

.palette-empty {
  padding: 24px;
  text-align: center;
  color: var(--color-text-muted, #9ca3af);
}

.palette-category {
  padding: 8px 12px 4px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-muted, #9ca3af);
}

.palette-item {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 10px 12px;
  border: none;
  background: transparent;
  border-radius: 8px;
  cursor: pointer;
  text-align: left;
  font-size: 14px;
  color: var(--color-text, #111);
  transition: background 0.1s;
}

.palette-item:hover,
.palette-item.selected {
  background: var(--color-primary-light, #eff6ff);
}

.palette-item.selected {
  background: var(--color-primary, #3b82f6);
  color: white;
}

.palette-item.selected .item-shortcut kbd {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.item-icon {
  font-size: 16px;
  width: 24px;
  text-align: center;
}

.item-label {
  flex: 1;
}

.item-shortcut kbd {
  padding: 2px 6px;
  font-size: 11px;
  background: var(--color-muted, #f3f4f6);
  border-radius: 4px;
  color: var(--color-text-muted, #6b7280);
}

.palette-footer {
  display: flex;
  gap: 16px;
  padding: 12px 16px;
  border-top: 1px solid var(--color-border, #e5e7eb);
  font-size: 12px;
  color: var(--color-text-muted, #9ca3af);
}

.palette-footer kbd {
  padding: 2px 4px;
  font-size: 10px;
  background: var(--color-muted, #f3f4f6);
  border-radius: 3px;
  margin-right: 4px;
}

/* Transitions */
.palette-enter-active,
.palette-leave-active {
  transition: opacity 0.15s ease;
}

.palette-enter-active .command-palette,
.palette-leave-active .command-palette {
  transition: transform 0.15s ease, opacity 0.15s ease;
}

.palette-enter-from,
.palette-leave-to {
  opacity: 0;
}

.palette-enter-from .command-palette,
.palette-leave-to .command-palette {
  transform: scale(0.95) translateY(-10px);
  opacity: 0;
}

/* Scrollbar styling */
.palette-results::-webkit-scrollbar {
  width: 6px;
}

.palette-results::-webkit-scrollbar-track {
  background: transparent;
}

.palette-results::-webkit-scrollbar-thumb {
  background: var(--color-border, #e5e7eb);
  border-radius: 3px;
}

.palette-results::-webkit-scrollbar-thumb:hover {
  background: var(--color-text-muted, #9ca3af);
}
</style>
