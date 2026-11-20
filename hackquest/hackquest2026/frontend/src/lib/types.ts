export type Member = { name: string; email: string; mobile: string; is_leader?: boolean }
export type Team = {
  id: number; name: string; code: string; code_active: boolean; status: string
  college: string; department: string; semester: string; members: Member[]
}
export type RoundView = {
  number: number; name: string; duration_minutes: number; state: string
  blurb?: string
}
export type Challenge = {
  slug: string; round: number; order: number; title: string; category: string
  difficulty: string; points: number; flag_format: string; status: string
  hint_count: number; attachment_name: string | null; prerequisite: string | null
  description?: string; solved?: boolean; hints?: { index: number; text: string; used: boolean }[]
}
export type TeamState = {
  server_now: string
  rounds: { number: number; name: string; state: string; remaining_seconds: number | null; allowed: boolean }[]
  solved: number[]; score: number
}
export type AdminChallenge = Challenge & {
  id: number; round_number: number; flag: string; hint1: string; hint2: string
  solution: string; concept: string; enabled: boolean; attachment_text: string | null
}
export type ScoreRow = {
  rank: number; team: string; team_id: number; members: string
  round1: number; round2: number; round3: number; final: number
  total: number; solved: number; code: string
}
