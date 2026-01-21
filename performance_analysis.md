
## 9. Appendix: Remote Environment Test Commands
Stress tests performed on the deployed instance (`http://110.40.153.38:5007/`):

1. **10 Concurrency**:
   ```bash
   ab -n 1000 -c 10 http://110.40.153.38:5007/
   ```

2. **100 Concurrency**:
   ```bash
   ab -n 1000 -c 100 http://110.40.153.38:5007/
   ```
