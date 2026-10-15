export type Role = "team" | "organizer";

export type Me =
  | { authenticated: false }
  | {
      authenticated: true;
      role: Role;
      must_change_password?: boolean;
      team_name?: string;
      team_code?: string;
      status?: string;
      email_verified?: boolean;
      members?: { name: string; email: string; is_leader: boolean }[];
      username?: string;
      full_name?: string;
      email?: string;
      admin_role?: string;
    };

export type RoundSummary = {
  number: number;
  slug: string;
  name: string;
  blurb: string;
  state: "locked" | "open" | "closed";
  challenges_total: number;
  challenges_solved: number;
  unlocked: boolean;
};

export type ChallengeView = {
  key: string;
  title: string;
  category: string;
  difficulty: string;
  description: string;
  answer_format: string;
  initial_clue: string;
  points: number | null;
  hints: string[];
  hints_unlocked: number;
  hints_used: number;
  hint_penalty: number;
  solved: boolean;
  explanation?: string;
};

export type RoundDetail = {
  number: number;
  slug: string;
  name: string;
  blurb: string;
  state: "locked" | "open" | "closed";
  challenges_total: number;
  challenges_solved: number;
  challenges: ChallengeView[];
  explanation: string | null;
};

export type Scoring = {
  mode: "tier" | "normalized";
  max_possible: number;
  nominal_ceiling: number;
  weights: Record<string, string>;
  rounding_policy: string;
};

export type LeaderRow = {
  rank: number;
  team: string;
  team_code: string;
  solved: number;
  attempted: number;
  points: number;
  violations: number;
  disqualified: boolean;
  status: "clean" | "flagged" | "disqualified";
  last_solve_at?: string | null;
};

export type RoundsResponse = {
  rounds: RoundSummary[];
  scoring: Scoring;
  state: {
    disqualified: boolean;
    competition: "pending" | "running" | "paused" | "ended";
    results_frozen: boolean;
    results_published: boolean;
  };
  event_datetime: string;
  event_timezone: string;
};

export type SubmitResult = {
  correct: boolean;
  points: number;
  attempts: number;
  already_accepted: boolean;
  unlocked: { round: number; code: string; already: boolean } | null;
  test_detail?: { passed: number; total: number; correct: boolean } | null;
};

export type ViolationResult = {
  ok: boolean;
  violations: number;
  limit: number;
  disqualified: boolean;
  notice?: string | null;
};