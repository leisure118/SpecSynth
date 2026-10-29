//@ logic integer sum_upto(integer n) = n*(n+1) / 2;
/*@
  lemma sum_rec: \forall integer n; n >=0 ==>
  sum_upto(n+1) == sum_upto(n)+n+1;
*/
long sum(int x) {
  if (x == 0) return 0;
  else return x + sum (x-1);
}

int main () {
  long i = sum(8);
  //@ assert i == 36;
}