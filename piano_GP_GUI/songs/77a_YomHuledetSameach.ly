\version "2.20.0"
\header {
\include "lilypond-book-preamble.ly"
   tagline = "" % removed
 }
\score {
 {
   \relative c'{\time 3/4 s2 g'8 g | a4 g c | b2 g8 g | a4 g d' | c2 g8 g | g'4 e c | b a f'8 f| e4 c d | c2 s4 \bar "|."} 

}
\layout {
  \context {
      \Score 
      proportionalNotationDuration =  #(ly:make-moment 1/5)
 }
 }
\midi {\tempo 4 = 60}
}
