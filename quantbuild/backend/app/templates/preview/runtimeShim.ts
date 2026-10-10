/**
 * Runtime shim: replaces the generated `entityConfig.ts` and `appInfo.ts`
 * modules inside the live-preview bundle.  The QuantBuild server injects
 * `window.__QB_PREVIEW_CONFIG__` when serving the preview page.
 */

export interface EntityFieldConfig {
  key: string;
  label: string;
  input: "text" | "number" | "checkbox" | "textarea" | "datetime-local" | "date";
  required: boolean;
}

export interface EntityConfig {
  resource: string;
  label: string;
  columns: { key: string; label: string }[];
  fields: EntityFieldConfig[];
}

export interface AppInfo {
  name: string;
  appType: string;
  features: string[];
}

interface PreviewConfig {
  entityConfigs: EntityConfig[];
  appInfo: AppInfo;
}

const injected: PreviewConfig = (window as unknown as { __QB_PREVIEW_CONFIG__: PreviewConfig })
  .__QB_PREVIEW_CONFIG__ ?? {
  entityConfigs: [],
  appInfo: { name: "Preview", appType: "Application", features: [] },
};

export const entityConfigs: EntityConfig[] = injected.entityConfigs;
export const appInfo: AppInfo = injected.appInfo;
