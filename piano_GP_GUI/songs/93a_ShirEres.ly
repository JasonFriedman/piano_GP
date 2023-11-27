\version "2.20.0"
\header {
\include "lilypond-book-preamble.ly"
   tagline = "" % removed
 }
\score {
 {
  \key f \major \relative c'{\numericTimeSignature a'2 c | g4. a8 bes2 | a4 a g8 f e f | g2 c, | a' c | g4. a8 bes2 | a4 a g8 a bes g | f1 | g2 g4 g a4. g8 f2 | c'2 bes4 a | g2 c,2 | a'2 c | g4. a8 bes2 | a4 a g8 a bes g | f1 \bar "|."}

}
\layout {
  \context {
      \Score 
      proportionalNotationDuration =  #(ly:make-moment 1/5)
 }
 }
\midi {\tempo 4 = 60}
}
