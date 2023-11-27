\version "2.20.0"
\header {
\include "lilypond-book-preamble.ly"
   tagline = "" % removed
 }
\score {
 {
  \key g \major \relative c'{\time 4/4 s2 s4 s8 g'8 | d'4 b8 g d'4 b8 g8 | d'8[ d] e[ e] d4 (b8) g8 | d'[ d] b[ g] d'[ d] b[ g] | d'[ d] e[ e] d4( b8) s8 \bar "|."} 

}
\layout {
  \context {
      \Score 
      proportionalNotationDuration =  #(ly:make-moment 1/5)
 }
 }
\midi {\tempo 4 = 60}
}
