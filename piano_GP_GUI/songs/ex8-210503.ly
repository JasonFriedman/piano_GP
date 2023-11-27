\version "2.20.0"
\header {
\include "lilypond-book-preamble.ly"
   tagline = "" % removed
 }
\score {
 {
  % first lesson ex.8
% Alfred's basic adult piano course, p. 9
% updated 3 May 2021

  \new PianoStaff 
  <<
    \new Staff = "upper"
\relative c' {
  	\clef treble
	\numericTimeSignature
  	\time 4/4
	e4 e f g | g f e d | c c d e | e d d2 | e4 e f g | g f e d | c c d e | d c c2 \bar "|."}
    \new Staff = "lower" 
\relative c {
  	\clef bass
	\numericTimeSignature
  	\time 4/4
   	R1 R1 R1 R1 R1 R1 R1 R1 \bar "|." }
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
