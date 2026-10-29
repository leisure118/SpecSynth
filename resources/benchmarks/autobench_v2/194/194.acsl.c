/*@
  requires \true;
  ensures 0 <= \result <= 1;
  ensures \result == 1 <==> (a + b + c == 180 && a > 0 && b > 0 && c > 0);
  assigns \nothing;
*/
int triangle(int a, int b, int c) {
    if ((a+b+c == 180) && a > 0 && b > 0 && c > 0) {
        return 1;
    } else {
        return 0;
    }
}

void check_validity() {
    int res = triangle(90, 45, 45);
    //@ assert res == 1;
    res = triangle(90, 145, 145);
    //@ assert res == 0;
}
