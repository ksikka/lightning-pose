import {ChangeDetectionStrategy, Component, EventEmitter, input, Input, Output} from '@angular/core';
import { Session } from '../../session.model';
import {SessionService} from '../../session.service';
import {Subscription} from 'rxjs';
import {RouterLink, RouterLinkActive} from '@angular/router';
import {MatListModule} from '@angular/material/list';
import {ScrollingModule} from '@angular/cdk/scrolling';

@Component({
  selector: 'app-viewer-left-panel',
  imports: [
    RouterLink,
    RouterLinkActive,
    MatListModule,
    ScrollingModule,
  ],
  templateUrl: './viewer-left-panel.component.html',
  styleUrl: './viewer-left-panel.component.css',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class ViewerLeftPanelComponent {

  constructor(private sessionService: SessionService) { }

  ngOnInit(): void {
    this.loadSessions();
  }

  selectedSession = input<Session | null>(null);
  private sessionsSubscription: Subscription | undefined;

  isLoading: boolean = false;
  errorMessage: string | null = null;

  sessions: Session[] = [];
  loadSessions(): void {
    this.isLoading = true;
    this.errorMessage = null;
    this.sessions = [];

    this.sessionsSubscription = this.sessionService.getAllSessions().subscribe({
      next: (loadedSessions) => {
        this.sessions = loadedSessions;
        this.isLoading = false;
      },
      error: (err) => {
        this.isLoading = false;
        console.error(err);
      },
      complete: () => {
      }
    });
  }
}

