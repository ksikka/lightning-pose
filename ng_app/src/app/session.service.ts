import { Injectable } from '@angular/core';
import {Observable, of} from 'rxjs';
import {Session} from './session.model';

@Injectable({
  providedIn: 'root'
})
export class SessionService {

  constructor() { }
  getAllSessions(): Observable<Session[]> {
    const mockSessions: Session[] = getUniqueSessionTemplates(dirList).map(templateName => {
      return { key: templateName.replace(/\.mp4$/, '') };
    });
    return of(mockSessions); // 'of' creates an Observable that emits the provided value and completes.
  }

}


const dirList = `05272019_fly3_0_R1C24_Cam-A_rot-ccw-0.06_sec.fine.mp4
05272019_fly3_0_R1C24_Cam-B_rot-ccw-0.06_sec.fine.mp4
05272019_fly3_0_R1C24_Cam-C_rot-ccw-0.06_sec.fine.mp4
05272019_fly3_0_R1C24_Cam-D_rot-ccw-0.06_sec.fine.mp4
05272019_fly3_0_R1C24_Cam-E_rot-ccw-0.06_sec.fine.mp4
05272019_fly3_0_R1C24_Cam-F_rot-ccw-0.06_sec.fine.mp4
05272019_fly3_0_R2C20_Cam-A_rot-cw-0.36_sec.fine.mp4
05272019_fly3_0_R2C20_Cam-B_rot-cw-0.36_sec.fine.mp4
05272019_fly3_0_R2C20_Cam-C_rot-cw-0.36_sec.fine.mp4
05272019_fly3_0_R2C20_Cam-D_rot-cw-0.36_sec.fine.mp4
05272019_fly3_0_R2C20_Cam-E_rot-cw-0.36_sec.fine.mp4
05272019_fly3_0_R2C20_Cam-F_rot-cw-0.36_sec.fine.mp4
05272019_fly3_0_R2C26_Cam-A_rot-ccw-0.18_sec.fine.mp4
05272019_fly3_0_R2C26_Cam-B_rot-ccw-0.18_sec.fine.mp4
05272019_fly3_0_R2C26_Cam-C_rot-ccw-0.18_sec.fine.mp4
05272019_fly3_0_R2C26_Cam-D_rot-ccw-0.18_sec.fine.mp4
05272019_fly3_0_R2C26_Cam-E_rot-ccw-0.18_sec.fine.mp4
05272019_fly3_0_R2C26_Cam-F_rot-ccw-0.18_sec.fine.mp4
05272019_fly3_0_R3C15_Cam-A_rot-cw-0_sec.fine.mp4
05272019_fly3_0_R3C15_Cam-B_rot-cw-0_sec.fine.mp4
05272019_fly3_0_R3C15_Cam-C_rot-cw-0_sec.fine.mp4
05272019_fly3_0_R3C15_Cam-D_rot-cw-0_sec.fine.mp4
05272019_fly3_0_R3C15_Cam-E_rot-cw-0_sec.fine.mp4
05272019_fly3_0_R3C15_Cam-F_rot-cw-0_sec.fine.mp4
05272019_fly4_0_R1C24_Cam-A_rot-ccw-0.06_sec.fine.mp4
05272019_fly4_0_R1C24_Cam-B_rot-ccw-0.06_sec.fine.mp4
05272019_fly4_0_R1C24_Cam-C_rot-ccw-0.06_sec.fine.mp4
05272019_fly4_0_R1C24_Cam-D_rot-ccw-0.06_sec.fine.mp4
05272019_fly4_0_R1C24_Cam-E_rot-ccw-0.06_sec.fine.mp4
05272019_fly4_0_R1C24_Cam-F_rot-ccw-0.06_sec.fine.mp4
05272019_fly4_0_R2C14_Cam-A_str-ccw-0.72_sec.fine.mp4
05272019_fly4_0_R2C14_Cam-B_str-ccw-0.72_sec.fine.mp4
05272019_fly4_0_R2C14_Cam-C_str-ccw-0.72_sec.fine.mp4
05272019_fly4_0_R2C14_Cam-D_str-ccw-0.72_sec.fine.mp4
05272019_fly4_0_R2C14_Cam-E_str-ccw-0.72_sec.fine.mp4
05272019_fly4_0_R2C14_Cam-F_str-ccw-0.72_sec.fine.mp4
05272019_fly4_0_R2C18_Cam-A_rot-cw-0.09_sec.fine.mp4
05272019_fly4_0_R2C18_Cam-B_rot-cw-0.09_sec.fine.mp4
05272019_fly4_0_R2C18_Cam-C_rot-cw-0.09_sec.fine.mp4
05272019_fly4_0_R2C18_Cam-D_rot-cw-0.09_sec.fine.mp4
05272019_fly4_0_R2C18_Cam-E_rot-cw-0.09_sec.fine.mp4
05272019_fly4_0_R2C18_Cam-F_rot-cw-0.09_sec.fine.mp4
05272019_fly4_0_R2C26_Cam-A_rot-ccw-0.18_sec.fine.mp4
05272019_fly4_0_R2C26_Cam-B_rot-ccw-0.18_sec.fine.mp4
05272019_fly4_0_R2C26_Cam-C_rot-ccw-0.18_sec.fine.mp4
05272019_fly4_0_R2C26_Cam-D_rot-ccw-0.18_sec.fine.mp4
05272019_fly4_0_R2C26_Cam-E_rot-ccw-0.18_sec.fine.mp4
05272019_fly4_0_R2C26_Cam-F_rot-ccw-0.18_sec.fine.mp4
05272019_fly4_0_R3C16_Cam-A_rot-cw-0.03_sec.fine.mp4
05272019_fly4_0_R3C16_Cam-B_rot-cw-0.03_sec.fine.mp4
05272019_fly4_0_R3C16_Cam-C_rot-cw-0.03_sec.fine.mp4
05272019_fly4_0_R3C16_Cam-D_rot-cw-0.03_sec.fine.mp4
05272019_fly4_0_R3C16_Cam-E_rot-cw-0.03_sec.fine.mp4
05272019_fly4_0_R3C16_Cam-F_rot-cw-0.03_sec.fine.mp4
05272019_fly4_0_R3C26_Cam-A_rot-ccw-0.18_sec.fine.mp4
05272019_fly4_0_R3C26_Cam-B_rot-ccw-0.18_sec.fine.mp4
05272019_fly4_0_R3C26_Cam-C_rot-ccw-0.18_sec.fine.mp4
05272019_fly4_0_R3C26_Cam-D_rot-ccw-0.18_sec.fine.mp4
05272019_fly4_0_R3C26_Cam-E_rot-ccw-0.18_sec.fine.mp4
05272019_fly4_0_R3C26_Cam-F_rot-ccw-0.18_sec.fine.mp4
05272019_fly5_0_R1C12_Cam-A_str-ccw-0.18_sec.fine.mp4
05272019_fly5_0_R1C12_Cam-B_str-ccw-0.18_sec.fine.mp4
05272019_fly5_0_R1C12_Cam-C_str-ccw-0.18_sec.fine.mp4
05272019_fly5_0_R1C12_Cam-D_str-ccw-0.18_sec.fine.mp4
05272019_fly5_0_R1C12_Cam-E_str-ccw-0.18_sec.fine.mp4
05272019_fly5_0_R1C12_Cam-F_str-ccw-0.18_sec.fine.mp4
05272019_fly5_0_R1C5_Cam-A_str-cw-0.18_sec.fine.mp4
05272019_fly5_0_R1C5_Cam-B_str-cw-0.18_sec.fine.mp4
05272019_fly5_0_R1C5_Cam-C_str-cw-0.18_sec.fine.mp4
05272019_fly5_0_R1C5_Cam-D_str-cw-0.18_sec.fine.mp4
05272019_fly5_0_R1C5_Cam-E_str-cw-0.18_sec.fine.mp4
05272019_fly5_0_R1C5_Cam-F_str-cw-0.18_sec.fine.mp4
05272019_fly5_0_R2C16_Cam-A_rot-cw-0.03_sec.fine.mp4
05272019_fly5_0_R2C16_Cam-B_rot-cw-0.03_sec.fine.mp4
05272019_fly5_0_R2C16_Cam-C_rot-cw-0.03_sec.fine.mp4
05272019_fly5_0_R2C16_Cam-D_rot-cw-0.03_sec.fine.mp4
05272019_fly5_0_R2C16_Cam-E_rot-cw-0.03_sec.fine.mp4
05272019_fly5_0_R2C16_Cam-F_rot-cw-0.03_sec.fine.mp4
05272019_fly5_0_R2C5_Cam-A_str-cw-0.18_sec.fine.mp4
05272019_fly5_0_R2C5_Cam-B_str-cw-0.18_sec.fine.mp4
05272019_fly5_0_R2C5_Cam-C_str-cw-0.18_sec.fine.mp4
05272019_fly5_0_R2C5_Cam-D_str-cw-0.18_sec.fine.mp4
05272019_fly5_0_R2C5_Cam-E_str-cw-0.18_sec.fine.mp4
05272019_fly5_0_R2C5_Cam-F_str-cw-0.18_sec.fine.mp4
05272019_fly5_0_R3C15_Cam-A_rot-cw-0_sec.fine.mp4
05272019_fly5_0_R3C15_Cam-B_rot-cw-0_sec.fine.mp4
05272019_fly5_0_R3C15_Cam-C_rot-cw-0_sec.fine.mp4
05272019_fly5_0_R3C15_Cam-D_rot-cw-0_sec.fine.mp4
05272019_fly5_0_R3C15_Cam-E_rot-cw-0_sec.fine.mp4
05272019_fly5_0_R3C15_Cam-F_rot-cw-0_sec.fine.mp4
05272019_fly5_0_R3C19_Cam-A_rot-cw-0.18_sec.fine.mp4
05272019_fly5_0_R3C19_Cam-B_rot-cw-0.18_sec.fine.mp4
05272019_fly5_0_R3C19_Cam-C_rot-cw-0.18_sec.fine.mp4
05272019_fly5_0_R3C19_Cam-D_rot-cw-0.18_sec.fine.mp4
05272019_fly5_0_R3C19_Cam-E_rot-cw-0.18_sec.fine.mp4
05272019_fly5_0_R3C19_Cam-F_rot-cw-0.18_sec.fine.mp4`.split('\n');

function getUniqueSessionTemplates(filenames: string[]): string[] {
  // A Set will store only unique session templates
  const sessionTemplates = new Set<string>();

  // Regular expression to find "_Cam-" followed by a single uppercase letter A-F, followed by "_"
  // The [A-F] part ensures we only match the specified camera identifiers.
  const camPattern = /_Cam-[A-F]_/;

  for (const filename of filenames) {
    // Replace the matched pattern with "_Cam-N_"
    // If the pattern is not found in a filename, replace() will return the original string.
    const sessionTemplate = filename.replace(camPattern, "_Cam-N_");
    sessionTemplates.add(sessionTemplate);
  }

  // Convert the Set back to an array
  return Array.from(sessionTemplates);
}
