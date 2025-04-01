import { TestBed } from '@angular/core/testing';

import { ProjectMetadataService } from './project-metadata.service';

describe('ProjectMetadataServiceService', () => {
  let service: ProjectMetadataService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(ProjectMetadataService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
