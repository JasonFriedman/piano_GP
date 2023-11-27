\version "2.20.0"
\header {
\include "lilypond-book-preamble.ly"
   tagline = "" % removed
 }
\score {
 {
  % first lesson ex.5
% Thompson easiest piano course, part I, p. 18
% updated 3 May 2021

  \new PianoStaff 
  <<
    \new Staff = "upper" 
\relative c' {
  \clef treble
  \numericTimeSignature
  \time 4/4
  e4 d c d | e e e2 | d4 d d2 | e4 e e2 | e4 d c d | e e e c | d d e d | c1 \bar "|."}
    \new Staff = "lower" 
\relative c {
  \clef bass
  \numericTimeSignature
  \time 4/4
  R1 | R1 | R1 | R1 | R1 | R1 | R1 | R1 \bar "|." }
  >>

}
\layout {
  \context {
      \Score 
      proportionalNotationDuration =  #(ly:make-moment 1/5)
 }
 }
\midi {\tempo 4 = 60}
}
