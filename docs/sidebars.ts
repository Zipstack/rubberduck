import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

/**
 * Creating a sidebar enables you to:
 - create an ordered group of docs
 - render a sidebar for each doc of that group
 - provide next/previous navigation

 The sidebars can be generated from the filesystem, or explicitly defined here.

 Create as many sidebars as you want.
 */
const sidebars: SidebarsConfig = {
  docsSidebar: [
    'intro',
    'installation',
    {
      type: 'category',
      label: 'Usage Guide',
      items: [
        'usage/creating-proxies',
        'usage/managing-proxies',
        'usage/using-proxies',
      ],
    },
    {
      type: 'category',
      label: 'Provider-Specific Notes',
      items: [
        'providers/overview',
        'providers/bedrock',
      ],
    },
    'testing-client',
    'logging',
    'user-management',
    'advanced',
  ],
};

export default sidebars;
