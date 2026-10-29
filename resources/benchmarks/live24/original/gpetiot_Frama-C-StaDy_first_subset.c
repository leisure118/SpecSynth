void firstSubset(int s[], int n) {
 int k;
 for ( k = 0; k < n; k++) {
  s[k] = 0;
 }
}
int main(){
  int s[3];
  firstSubset(s, 3);
  //@ assert s[0] == 0 && s[1] == 0 && s[2] == 0;
}