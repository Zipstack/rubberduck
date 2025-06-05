/// <reference types="vitest/globals" />

import type { expect, describe, it, beforeEach, vi } from 'vitest';

declare global {
  const expect: typeof expect;
  const describe: typeof describe;
  const it: typeof it;
  const beforeEach: typeof beforeEach;
  const vi: typeof vi;
}