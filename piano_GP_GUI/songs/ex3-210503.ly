\version "2.20.0"
\header {
\include "lilypond-book-preamble.ly"
   tagline = "" % removed
 }
\score {
 {
  % first lesson ex.3
% Thompson easiest piano course, part I, p. 14
% updated 3 May 2021

  \new PianoStaff 
  <<
    \new Staff = "upper" 
\relative c' {
  \clef treble
  \numericTimeSignature
  \time 4/4
  R1 | R1 | R1 | R1 | R1 | R1 | R1 | R1 \bar "|."}
    \new Staff = "lower" 
\relative c {
  \clef bass
  \numericTimeSignature
  \time 4/4
  c'1 | b1 | c4 b c b | c2 c | c1 | b1 | c4 b c b | c2 c \bar "|." }
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
